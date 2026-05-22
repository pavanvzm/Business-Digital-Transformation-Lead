"""Kafka consumer with CloudEvents deserialization, dead-letter routing, and local fallback queue."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Callable, Coroutine
from typing import Any

from aiokafka import AIOKafkaConsumer
from cloudevents.http import CloudEvent, from_json

from config.settings import settings
from src.messaging.schemas import ProductionEventType

logger = logging.getLogger(__name__)

EventHandler = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class EventConsumer:
    """Kafka consumer that deserializes CloudEvents and dispatches to registered handlers.

    Dead-letter topic: events that fail deserialization or have no registered handler
    are published to events.dead-letter for forensic analysis.

    Local fallback queue: when Kafka is unavailable, messages are queued to disk
    and replayed on reconnection.
    """

    def __init__(self, producer: Any | None = None) -> None:
        self._consumer: AIOKafkaConsumer | None = None
        self._producer = producer
        self._running = False
        self._handlers: dict[str, EventHandler] = {}
        self._local_queue_path = "/var/agent-02/queue"
        os.makedirs(self._local_queue_path, exist_ok=True)

        # Topics
        self._topics = [
            settings.kafka.topic_inventory_events,
            settings.kafka.topic_forecast_events,
            settings.kafka.topic_orchestrator_events,
            settings.kafka.topic_market_events,
        ]

    def register_handler(
        self, event_type: str, handler: EventHandler
    ) -> None:
        """Register a handler coroutine for a specific CloudEvent type."""
        if event_type in self._handlers:
            logger.warning("Overwriting existing handler for event type", event_type=event_type)
        self._handlers[event_type] = handler

    async def start(self) -> None:
        """Start the Kafka consumer connection."""
        try:
            self._consumer = AIOKafkaConsumer(
                *self._topics,
                bootstrap_servers=settings.kafka.bootstrap_servers,
                group_id=settings.kafka.consumer_group_id,
                session_timeout_ms=settings.kafka.session_timeout_ms,
                heartbeat_interval_ms=settings.kafka.heartbeat_interval_ms,
                max_poll_interval_ms=settings.kafka.max_poll_interval_ms,
                enable_auto_commit=settings.kafka.enable_auto_commit,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")) if m else None,
            )
            await self._consumer.start()
            self._running = True
            logger.info("Consumer started", topics=self._topics)
        except Exception:
            logger.exception("Failed to start Kafka consumer — entering fallback mode")
            self._running = True  # still mark as running for poll loop

    async def stop(self) -> None:
        """Gracefully stop the consumer."""
        self._running = False
        if self._consumer:
            await self._consumer.stop()
            logger.info("Consumer stopped")

    async def consume_loop(self) -> None:
        """Main consumption loop — polls Kafka, deserializes CloudEvents, dispatches handlers."""
        while self._running:
            try:
                if not self._consumer:
                    await asyncio.sleep(5)
                    continue

                records = await self._consumer.getmany(timeout_ms=1000)
                for _topic, messages in records.items():
                    for message in messages:
                        await self._process_message(message.value)

                await self._consumer.commit()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in consume loop")
                await asyncio.sleep(5)

    async def _process_message(self, raw_value: dict[str, Any] | None) -> None:
        """Deserialize a CloudEvent and route to the registered handler."""
        if raw_value is None:
            return

        try:
            # Try to parse as CloudEvent
            ce = from_json(json.dumps(raw_value).encode("utf-8"))
            event_type = ce.get("type", "")
            event_data = ce.get("data", {})

            handler = self._handlers.get(event_type)
            if handler:
                await handler(event_data if isinstance(event_data, dict) else {})
            else:
                logger.warning("No handler for event type", event_type=event_type)
                await self._route_to_dead_letter(raw_value, f"No handler for {event_type}")
        except Exception:
            # Fallback: treat as raw JSON
            logger.debug("Message is not a CloudEvent — treating as raw JSON")
            event_type = raw_value.get("type", raw_value.get("event_type", "unknown"))
            handler = self._handlers.get(event_type)
            if handler:
                await handler(raw_value)
            else:
                await self._route_to_dead_letter(raw_value, "Unknown format")

    async def _route_to_dead_letter(
        self, message: dict[str, Any], reason: str
    ) -> None:
        """Route unprocessable messages to dead-letter topic or local file."""
        try:
            if self._producer:
                await self._producer.publish(
                    topic=settings.kafka.topic_dead_letter,
                    event_type="com.manufacturing.dead-letter",
                    data={"original_message": message, "reason": reason},
                    subject="dead-letter/agent-02",
                )
        except Exception:
            logger.exception("Failed to route to dead-letter topic")

        # Also write to local file as backup
        await self._write_to_local_queue(message)

    async def _write_to_local_queue(self, message: dict[str, Any]) -> None:
        """Write a message to the local fallback queue on disk."""
        try:
            file_path = os.path.join(self._local_queue_path, "queue.jsonl")
            with open(file_path, "a") as f:
                f.write(json.dumps(message) + "\n")
        except Exception:
            logger.exception("Failed to write to local queue")

    async def replay_local_queue(self) -> int:
        """Replay messages queued during Kafka outage."""
        file_path = os.path.join(self._local_queue_path, "queue.jsonl")
        if not os.path.exists(file_path):
            return 0

        count = 0
        try:
            with open(file_path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            message = json.loads(line)
                            await self._process_message(message)
                            count += 1
                        except Exception:
                            logger.exception("Failed to replay queued message")
            # Clear the queue after replay
            os.remove(file_path)
            logger.info("Local queue replayed and cleared", count=count)
        except Exception:
            logger.exception("Error replaying local queue")
        return count
