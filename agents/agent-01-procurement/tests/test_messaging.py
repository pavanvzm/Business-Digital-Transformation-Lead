"""Tests for messaging schemas — CloudEvents, payload validation, JSON serialization."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from src.messaging.schemas import (
    CloudEvent,
    PriceAlertPayload,
    PORecommendationPayload,
    VendorScorecardPayload,
    SourcingOptionPayload,
    ForecastDemandPayload,
    InventorySnapshotPayload,
    OrchestratorCommand,
    PriceThreshold,
    POStatus,
)


class TestCloudEvent:
    """CloudEvents 1.0 envelope validation."""

    def test_cloud_event_creation(self) -> None:
        """Basic CloudEvent creation."""
        event = CloudEvent(
            type="com.manufacturing.test",
            data={"key": "value"},
        )

        assert event.specversion == "1.0"
        assert event.type == "com.manufacturing.test"
        assert event.source == "/agents/procurement-agent/v1"
        assert event.id is not None
        assert event.time is not None
        assert event.datacontenttype == "application/ld+json"

    def test_cloud_event_serialization(self) -> None:
        """CloudEvent serializes to JSON."""
        event = CloudEvent(
            type="com.manufacturing.test",
            data={"key": "value"},
        )

        json_str = event.to_json()
        assert isinstance(json_str, str)
        assert "specversion" in json_str
        assert "com.manufacturing.test" in json_str

    def test_cloud_event_utc_timezone(self) -> None:
        """Time without tzinfo is converted to UTC."""
        naive_time = datetime(2026, 5, 21, 12, 0, 0)
        event = CloudEvent(
            type="com.manufacturing.test",
            data={},
            time=naive_time,
        )
        assert event.time.tzinfo is not None


class TestPriceAlertPayload:
    """Price alert event validation."""

    def test_price_alert_defaults(self) -> None:
        alert = PriceAlertPayload(
            material_id="MAT-COPPER-001",
            material_name="Copper",
            current_price=8.50,
            previous_price=7.50,
            percent_change=13.33,
            threshold_breached=PriceThreshold.CRITICAL,
        )

        assert alert.unit == "USD/kg"
        assert alert.confidence == 0.95
        assert alert.data_sources == ["LME", "Bloomberg", "S&P Global"]
        assert alert.@context is not None  # type: ignore[attr-defined]

    def test_price_alert_threshold_mapping(self) -> None:
        """Threshold enum values."""
        assert PriceThreshold.WARNING.value == "warning"
        assert PriceThreshold.CRITICAL.value == "critical"
        assert PriceThreshold.NORMAL.value == "normal"


class TestPORecommendation:
    """PO recommendation payload validation."""

    def test_po_recommendation_defaults(self) -> None:
        po = PORecommendationPayload(
            po_id="PO-ABC123",
            vendor_id="V001",
            vendor_name="Test Supplier",
            material_id="MAT-STEEL-001",
            material_name="Steel Coil",
            quantity=1000.0,
            unit="kg",
            unit_price=850.0,
            total_value=850_000.0,
            recommended_delivery_date="2026-06-15",
            reasoning="Test PO",
        )

        assert po.currency == "USD"
        assert po.status == POStatus.DRAFT
        assert po.confidence == 0.85
        assert not po.hitl_required

    def test_po_with_line_items(self) -> None:
        po = PORecommendationPayload(
            po_id="PO-MULTI-001",
            vendor_id="V002",
            vendor_name="Multi Item Supplier",
            material_id="MAT-001",
            material_name="Various",
            quantity=500.0,
            unit="kg",
            unit_price=100.0,
            total_value=50_000.0,
            recommended_delivery_date="2026-07-01",
            reasoning="Multi-item PO",
            line_items=[
                {"line_number": 1, "material_id": "MAT-A", "material_name": "Material A", "quantity": 200.0, "unit": "kg", "unit_price": 100.0, "total_price": 20000.0},
                {"line_number": 2, "material_id": "MAT-B", "material_name": "Material B", "quantity": 300.0, "unit": "kg", "unit_price": 100.0, "total_price": 30000.0},
            ],
        )

        assert len(po.line_items) == 2


class TestVendorScorecardPayload:
    """Vendor scorecard payload validation."""

    def test_vendor_scorecard(self) -> None:
        scorecard = VendorScorecardPayload(
            vendor_id="V001",
            vendor_name="Test Corp",
            period="2026-Q2",
            overall_score=85.5,
            metrics=[
                {"name": "Price Competitiveness", "score": 80.0, "weight": 0.25, "data_source": "market_prices"},
                {"name": "Quality Rating", "score": 90.0, "weight": 0.20, "data_source": "erp_quality"},
            ],
        )

        assert scorecard.overall_score == 85.5
        assert len(scorecard.metrics) == 2
        assert scorecard.trend == "stable"


class TestAlternativeSourcing:
    """Sourcing option payload validation."""

    def test_sourcing_options(self) -> None:
        options = SourcingOptionPayload(
            material_id="MAT-STEEL-001",
            material_name="Steel Plate",
            primary_vendor={"vendor_id": "V001", "vendor_name": "Primary Inc", "estimated_unit_price": 100.0, "lead_time_days": 14, "qualification_status": "pre_qualified"},
            alternatives=[
                {"vendor_id": "V002", "vendor_name": "Alt Inc", "estimated_unit_price": 90.0, "lead_time_days": 21, "qualification_status": "pre_qualified"},
            ],
            recommendation="Switch to Alt Inc for 10% savings",
            estimated_savings=10.0,
        )

        assert len(options.alternatives) == 1
        assert options.estimated_savings == 10.0
        assert options.switching_risk == "low"


class TestIncomingPayloads:
    """Payload deserialization for incoming events."""

    def test_forecast_demand(self) -> None:
        forecast = ForecastDemandPayload(
            forecast_id="FCAST-2026-06",
            product_line="Product Line A",
            material_requirements={"MAT-STEEL-001": 5000.0, "MAT-COPPER-001": 2000.0},
            forecast_month="2026-06",
            confidence_interval={"lower": 4500.0, "upper": 5500.0},
        )

        assert forecast.forecast_id == "FCAST-2026-06"
        assert len(forecast.material_requirements) == 2

    def test_inventory_snapshot(self) -> None:
        snapshot = InventorySnapshotPayload(
            material_id="MAT-STEEL-001",
            material_name="Steel Coil",
            current_stock=1500.0,
            safety_stock=500.0,
            reorder_point=1000.0,
            unit="kg",
            warehouse_location="WH-A-12",
        )

        assert snapshot.current_stock == 1500.0
        assert snapshot.reorder_point == 1000.0

    def test_orchestrator_command_pause(self) -> None:
        cmd = OrchestratorCommand(
            command_type="pause",
            reason="System maintenance",
        )

        assert cmd.command_type == "pause"
        assert cmd.target_agent == "agent-01"
        assert cmd.issued_by == "agent-09"

    def test_orchestrator_command_circuit_breaker(self) -> None:
        cmd = OrchestratorCommand(
            command_type="circuit_breaker_status",
            parameters={"open": True},
            reason="Kafka cluster unreachable",
        )

        assert cmd.parameters["open"] is True
