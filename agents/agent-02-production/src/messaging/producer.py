"""Kafka producer with CloudEvents serialization and dead-letter fallback."""

from __future__ import annotations

import json
import logging

from aiokafka import AIOKafkaProducer
from cloudevents.http import CloudEvent

from config.settings import settings

logger = logging.getLogger(__name__)


class EventProducer:
    """Kafka producer that serializes CloudEvents to the message bus.

    Writes to a dead-letter file queue if Kafka is unavailable.
    """

    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None
        self._connected = False

    async def start(self) -> None:
        """Start the Kafka producer connection."""
        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self._producer.start()
            self._connected = True
            logger.info("Producer started", bootstrap=settings.kafka.bootstrap_servers)
        except Exception:
            logger.exception("Failed to start Kafka producer — local queue fallback active")
            self._connected = False

    async def stop(self) -> None:
        """Gracefully stop the producer."""
        if self._producer:
            await self._producer.stop()
            self._connected = False
            logger.info("Producer stopped")

    async def publish(
        self,
        topic: str,
        event_type: str,
        data: dict,
        subject: str = "",
        source: str = "agent-02",
        dataschema: str = "manufacturing.mas.production.v1",
    ) -> None:
        """Publish a CloudEvent to a Kafka topic."""
        attributes = {
            "type": event_type,
            "source": source,
            "subject": subject,
            "dataschema": dataschema,
        }
        event = CloudEvent(attributes=attributes, data=data)

        if self._producer and self._connected:
            try:
                await self._producer.send(topic, value=event.to_json())
                logger.debug("Published event", topic=topic, type=event_type)
            except Exception:
                logger.exception("Failed to publish event to Kafka")
                await self._write_to_local_queue(event.to_json())
        else:
            logger.warning("Producer not connected — queuing message locally")
            await self._write_to_local_queue(event.to_json())

    async def _write_to_local_queue(self, message: bytes) -> None:
        """Fallback: write message to local file queue."""
        import os

        queue_path = "/var/agent-02/queue"
        os.makedirs(queue_path, exist_ok=True)
        file_path = os.path.join(queue_path, "producer_queue.jsonl")
        try:
            with open(file_path, "ab") as f:
                f.write(message + b"\n")
        except Exception:
            logger.exception("Failed to write to local producer queue")

    # ──────────────────────────────────────────────
    # Convenience publishers for Agent-02
    # ──────────────────────────────────────────────

    async def publish_oee_report(
        self,
        data: dict,
        subject: str = "",
    ) -> None:
        """Publish an OEE report event to the production events topic."""
        await self.publish(
            topic=settings.kafka.topic_production_events,
            event_type="com.manufacturing.production.oee-report",
            data=data,
            subject=subject,
        )

    async def publish_quality_alert(
        self,
        data: dict,
        subject: str = "",
        hitl_required: bool = False,
    ) -> None:
        """Publish a quality alert event."""
        await self.publish(
            topic=settings.kafka.topic_production_events,
            event_type="com.manufacturing.production.quality-alert",
            data={"hitl_required": hitl_required, **data},
            subject=subject,
        )

    async def publish_production_schedule(
        self,
        data: dict,
        subject: str = "",
    ) -> None:
        """Publish a production schedule event."""
        await self.publish(
            topic=settings.kafka.topic_production_events,
            event_type="com.manufacturing.production.schedule",
            data=data,
            subject=subject,
        )

    async def publish_maintenance_trigger(
        self,
        data: dict,
        subject: str = "",
    ) -> None:
        """Publish a predictive maintenance trigger event."""
        await self.publish(
            topic=settings.kafka.topic_production_events,
            event_type="com.manufacturing.production.maintenance-trigger",
            data=data,
            subject=subject,
        )

    async def publish_bottleneck_analysis(
        self,
        data: dict,
        subject: str = "",
    ) -> None:
        """Publish a bottleneck analysis event."""
        await self.publish(
            topic=settings.kafka.topic_production_events,
            event_type="com.manufacturing.production.bottleneck-analysis",
            data=data,
            subject=subject,
        )

    async def publish_yield_recommendation(
        self,
        data: dict,
        subject: str = "",
    ) -> None:
        """Publish a yield optimization recommendation."""
        await self.publish(
            topic=settings.kafka.topic_production_events,
            event_type="com.manufacturing.production.yield-recommendation",
            data=data,
            subject=subject,
        )
