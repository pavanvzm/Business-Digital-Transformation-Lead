"""Kafka event producer with CloudEvents formatting, idempotent delivery, and retry.

Produces to:
  - events.procurement (Agent-01 → Agents 02,03,06,07,09)
  - events.dead-letter (failed messages from consumer)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import orjson
from aiokafka import AIOKafkaProducer
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings

logger = logging.getLogger(__name__)


class EventProducer:
    """Idempotent Kafka producer with CloudEvents envelope and retry logic."""

    def __init__(self) -> None:
        self._settings = settings.kafka
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        """Initialize and connect the Kafka producer."""
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._settings.bootstrap_servers,
            enable_idempotence=True,
            acks="all",  # Wait for all in-sync replicas
            compression_type="snappy",
            max_request_size=10485760,  # 10 MB
            value_serializer=lambda v: orjson.dumps(v),
        )
        await self._producer.start()
        logger.info("EventProducer started")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def publish(
        self,
        topic: str,
        event_type: str,
        data: dict[str, Any],
        subject: str | None = None,
        source: str = "/agents/procurement-agent/v1",
        data_ref: str | None = None,
    ) -> str:
        """Publish a CloudEvents-formatted message to Kafka.

        Args:
            topic: Kafka topic name.
            event_type: CloudEvent type (e.g., 'com.manufacturing.procurement.price-alert').
            data: JSON-LD payload.
            subject: Optional CloudEvent subject (e.g., 'raw-material/copper/price-alert').
            source: CloudEvent source identifier.
            data_ref: Optional URI reference for large payloads.

        Returns:
            str: The event ID for tracing.

        Raises:
            RuntimeError: If producer not started.
        """
        if not self._producer:
            raise RuntimeError("Producer not started. Call start() first.")

        event_id = str(uuid4())
        now = datetime.now(timezone.utc)

        envelope = {
            "specversion": "1.0",
            "type": event_type,
            "source": source,
            "id": event_id,
            "time": now.isoformat(),
            "datacontenttype": "application/ld+json",
            "subject": subject,
            "data": data,
        }

        if data_ref:
            envelope["dataref"] = data_ref

        await self._producer.send(topic, value=envelope)
        logger.debug(
            "Event published",
            event_id=event_id,
            topic=topic,
            event_type=event_type,
            subject=subject,
        )
        return event_id

    async def publish_price_alert(
        self,
        data: dict[str, Any],
        subject: str | None = None,
    ) -> str:
        """Convenience method to publish a price alert event."""
        return await self.publish(
            topic=self._settings.topic_procurement_events,
            event_type="com.manufacturing.procurement.price-alert",
            data=data,
            subject=subject,
        )

    async def publish_po_recommendation(
        self,
        data: dict[str, Any],
        subject: str | None = None,
        hitl_required: bool = False,
    ) -> str:
        """Convenience method to publish a PO recommendation."""
        data["hitl_required"] = hitl_required
        return await self.publish(
            topic=self._settings.topic_procurement_events,
            event_type="com.manufacturing.procurement.po-recommendation",
            data=data,
            subject=subject,
        )

    async def publish_vendor_scorecard(
        self,
        data: dict[str, Any],
        subject: str | None = None,
    ) -> str:
        """Convenience method to publish a vendor scorecard."""
        return await self.publish(
            topic=self._settings.topic_procurement_events,
            event_type="com.manufacturing.procurement.vendor-scorecard",
            data=data,
            subject=subject,
        )

    async def publish_sourcing_options(
        self,
        data: dict[str, Any],
        subject: str | None = None,
    ) -> str:
        """Convenience method to publish alternative sourcing options."""
        return await self.publish(
            topic=self._settings.topic_procurement_events,
            event_type="com.manufacturing.procurement.sourcing-options",
            data=data,
            subject=subject,
        )

    async def stop(self) -> None:
        """Gracefully stop the producer."""
        if self._producer:
            await self._producer.stop()
            logger.info("EventProducer stopped")
