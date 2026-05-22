"""Kafka event consumer with CloudEvents deserialization, retry, and dead-letter routing.

Consumes from:
  - events.market (Agent-05): competitor pricing, commodity prices
  - events.forecast (Agent-06): demand forecasts, BOM requirements
  - events.inventory (Agent-03): raw material stock levels
  - events.orchestrator (Agent-09): governance commands, HITL responses
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import orjson
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from src.messaging.producer import EventProducer

logger = logging.getLogger(__name__)

MessageHandler = Callable[[dict[str, Any]], Awaitable[None]]


class EventConsumer:
    """Asynchronous Kafka consumer with retry, dead-letter routing, and fallback queue."""

    def __init__(self, producer: EventProducer | None = None) -> None:
        self._settings = settings.kafka
        self._agent_settings = settings
        self._consumer: AIOKafkaConsumer | None = None
        self._producer = producer or EventProducer()
        self._handlers: dict[str, list[MessageHandler]] = {}
        self._fallback_queue_path = Path("/var/agent-01/queue")
        self._running = False

        # Ensure fallback queue directory exists
        self._fallback_queue_path.mkdir(parents=True, exist_ok=True)

    async def start(self) -> None:
        """Initialize Kafka consumer and connect to brokers."""
        self._consumer = AIOKafkaConsumer(
            self._settings.topic_market_events,
            self._settings.topic_forecast_events,
            self._settings.topic_inventory_events,
            self._settings.topic_orchestrator_events,
            bootstrap_servers=self._settings.bootstrap_servers,
            group_id=self._settings.consumer_group_id,
            session_timeout_ms=self._settings.session_timeout_ms,
            heartbeat_interval_ms=self._settings.heartbeat_interval_ms,
            max_poll_interval_ms=self._settings.max_poll_interval_ms,
            enable_auto_commit=self._settings.enable_auto_commit,
            value_deserializer=lambda v: orjson.loads(v) if v else None,
        )
        await self._consumer.start()
        # Start producer for dead-letter publishing
        await self._producer.start()
        self._running = True
        logger.info(
            "EventConsumer started",
            topics=[
                self._settings.topic_market_events,
                self._settings.topic_forecast_events,
                self._settings.topic_inventory_events,
                self._settings.topic_orchestrator_events,
            ],
        )

    def register_handler(self, event_type: str, handler: MessageHandler) -> None:
        """Register a handler for a specific CloudEvent type."""
        self._handlers.setdefault(event_type, []).append(handler)
        logger.debug("Handler registered", event_type=event_type, handler=handler.__name__)

    async def consume_loop(self) -> None:
        """Main consumption loop: poll, dispatch, commit."""
        if not self._consumer:
            raise RuntimeError("Consumer not started. Call start() first.")

        try:
            async for msg in self._consumer:
                try:
                    await self._dispatch_event(msg.topic, msg.value, msg.key)
                    await self._consumer.commit()
                except Exception:
                    logger.exception("Failed to process message", topic=msg.topic, offset=msg.offset)
                    await self._route_to_dead_letter(msg.topic, msg.value, msg.key)
        finally:
            self._running = False

    async def _dispatch_event(self, topic: str, value: dict | None, key: bytes | None) -> None:
        """Deserialize CloudEvent and dispatch to registered handlers."""
        if value is None:
            logger.warning("Received null message", topic=topic)
            return

        # Extract CloudEvent type
        event_type = value.get("type", topic)
        data = value.get("data", value)

        handlers = self._handlers.get(event_type, [])
        if not handlers:
            # Try topic-based routing
            topic_handlers = self._handlers.get(topic, [])
            if not topic_handlers:
                logger.debug("No handlers registered for event", event_type=event_type, topic=topic)
                return
            handlers = topic_handlers

        for handler in handlers:
            await handler(data)

    async def _route_to_dead_letter(self, topic: str, value: dict | None, key: bytes | None) -> None:
        """Route failed messages to dead-letter queue or local fallback."""
        if self._producer and self._producer._producer:
            try:
                dlq_message = {
                    "specversion": "1.0",
                    "type": "com.manufacturing.dead-letter",
                    "source": "/agents/procurement-agent/v1",
                    "subject": topic,
                    "time": None,  # will be set by producer
                    "datacontenttype": "application/json",
                    "data": {
                        "original_topic": topic,
                        "original_message": value,
                        "error": "Handler execution failed",
                        "timestamp": None,
                    },
                }
                await self._producer.publish(
                    topic=self._settings.topic_dead_letter,
                    event_type="com.manufacturing.dead-letter",
                    data=dlq_message["data"],
                    subject=topic,
                )
                logger.info("Message routed to dead-letter queue", topic=topic)
            except Exception:
                # Kafka unavailable — fall back to local file queue
                self._fallback_to_local_queue(topic, value)
        else:
            self._fallback_to_local_queue(topic, value)

    def _fallback_to_local_queue(self, topic: str, value: dict | None) -> None:
        """Persist message to local file queue for replay when Kafka reconnects."""
        import time
        filename = self._fallback_queue_path / f"{int(time.time())}_{topic.replace('.', '_')}.json"
        try:
            with open(filename, "w") as f:
                json.dump({"topic": topic, "value": value, "retry_count": 0}, f)
            logger.warning("Message queued locally (Kafka unavailable)", path=str(filename))
        except OSError:
            logger.exception("Failed to write local fallback queue")

    async def replay_local_queue(self) -> int:
        """Replay messages from local fallback queue when Kafka is restored."""
        replayed = 0
        for filepath in sorted(self._fallback_queue_path.glob("*.json")):
            try:
                with open(filepath) as f:
                    msg = json.load(f)
                # Re-process through dispatch
                await self._dispatch_event(msg["topic"], msg["value"], None)
                filepath.unlink()  # Remove after successful replay
                replayed += 1
                logger.info("Replayed queued message", path=str(filepath))
            except Exception:
                logger.exception("Failed to replay queued message", path=str(filepath))
                # Increment retry count
                try:
                    with open(filepath) as f:
                        msg = json.load(f)
                    msg["retry_count"] = msg.get("retry_count", 0) + 1
                    if msg["retry_count"] > 3:
                        logger.error("Max retries exceeded for queued message", path=str(filepath))
                        filepath.rename(filepath.with_suffix(".failed"))
                    else:
                        with open(filepath, "w") as f:
                            json.dump(msg, f)
                except OSError:
                    pass
        return replayed

    async def stop(self) -> None:
        """Gracefully stop consumer and producer."""
        self._running = False
        if self._consumer:
            await self._consumer.stop()
        await self._producer.stop()
        logger.info("EventConsumer stopped")
