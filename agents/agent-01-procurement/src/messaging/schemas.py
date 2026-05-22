"""CloudEvents + JSON-LD message schemas for Procurement Agent.

All messages conform to CloudEvents 1.0 specification with JSON-LD @context
for semantic interoperability across the MAS ecosystem.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────────────────────
# CloudEvent Envelope
# ──────────────────────────────────────────────


class CloudEvent(BaseModel):
    """CloudEvents 1.0 envelope with JSON-LD payload."""

    specversion: Literal["1.0"] = "1.0"
    type: str
    source: str = "/agents/procurement-agent/v1"
    id: str = Field(default_factory=lambda: str(uuid4()))
    time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    datacontenttype: str = "application/ld+json"
    subject: str | None = None
    data: dict[str, Any]
    dataref: str | None = None  # URI for large payloads stored externally

    @field_validator("time")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)

    def to_json(self) -> str:
        """Serialize to JSON using orjson for performance."""
        import orjson
        return orjson.dumps(self.model_dump(mode="json")).decode()


# ──────────────────────────────────────────────
# Price Alert Events
# ──────────────────────────────────────────────


class PriceThreshold(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


class PriceAlertPayload(BaseModel):
    """Payload for material price spike detection."""

    @context: dict[str, str] = Field(
        default={
            "schema": "https://schema.org/",
            "mas": "https://manufacturing.mas/context/1.0",
        },
        alias="@context",
    )
    type: str = Field(default="mas:PriceAlert", alias="@type")
    material_id: str
    material_name: str
    current_price: float
    unit: str = "USD/kg"
    previous_price: float
    percent_change: float
    threshold_breached: PriceThreshold
    threshold_config: dict[str, float] = {"warning": 5.0, "critical": 10.0}
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    data_sources: list[str] = ["LME", "Bloomberg", "S&P Global"]
    recommended_actions: list[str] = []
    business_impact: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None


# ──────────────────────────────────────────────
# Purchase Order Events
# ──────────────────────────────────────────────


class POStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    IN_TRANSIT = "in_transit"
    PARTIALLY_RECEIVED = "partially_received"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class LineItem(BaseModel):
    line_number: int
    material_id: str
    material_name: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    expected_delivery_date: str | None = None


class PORecommendationPayload(BaseModel):
    """Purchase order recommendation from Procurement Agent."""

    @context: dict[str, str] = Field(
        default={
            "schema": "https://schema.org/",
            "mas": "https://manufacturing.mas/context/1.0",
        },
        alias="@context",
    )
    type: str = Field(default="mas:PORecommendation", alias="@type")
    po_id: str
    vendor_id: str
    vendor_name: str
    material_id: str
    material_name: str
    quantity: float
    unit: str
    unit_price: float
    total_value: float
    currency: str = "USD"
    recommended_delivery_date: str
    status: POStatus = POStatus.DRAFT
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    reasoning: str
    alternatives: list[str] = []
    hitl_required: bool = False
    hitl_ticket_id: str | None = None
    provenance: dict[str, Any] | None = None
    line_items: list[LineItem] = []


# ──────────────────────────────────────────────
# Vendor Scorecard Events
# ──────────────────────────────────────────────


class VendorScoreMetric(BaseModel):
    name: str
    score: float = Field(ge=0.0, le=100.0)
    weight: float = Field(ge=0.0, le=1.0)
    data_source: str
    notes: str | None = None


class VendorScorecardPayload(BaseModel):
    """Vendor performance scorecard with 15 metrics."""

    @context: dict[str, str] = Field(
        default={
            "schema": "https://schema.org/",
            "mas": "https://manufacturing.mas/context/1.0",
        },
        alias="@context",
    )
    type: str = Field(default="mas:VendorScorecard", alias="@type")
    vendor_id: str
    vendor_name: str
    period: str  # "2026-Q2"
    overall_score: float = Field(ge=0.0, le=100.0)
    metrics: list[VendorScoreMetric] = []
    category: str = "general"  # general, critical_raw_materials, commodity, packaging
    trend: Literal["improving", "stable", "declining"] = "stable"
    previous_score: float | None = None
    risk_flags: list[str] = []
    recommendation: str | None = None
    provenance: dict[str, Any] | None = None


# ──────────────────────────────────────────────
# Alternative Sourcing Events
# ──────────────────────────────────────────────


class AlternativeSource(BaseModel):
    vendor_id: str
    vendor_name: str
    estimated_unit_price: float
    lead_time_days: int
    quality_rating: float | None = None
    esg_score: float | None = None
    qualification_status: str = "pre_qualified"  # pre_qualified, pending, disqualified
    risk_flags: list[str] = []


class SourcingOptionPayload(BaseModel):
    """Alternative sourcing analysis output."""

    @context: dict[str, str] = Field(
        default={
            "schema": "https://schema.org/",
            "mas": "https://manufacturing.mas/context/1.0",
        },
        alias="@context",
    )
    type: str = Field(default="mas:SourcingOptions", alias="@type")
    material_id: str
    material_name: str
    primary_vendor: AlternativeSource
    alternatives: list[AlternativeSource]
    recommendation: str
    estimated_savings: float | None = None
    switching_risk: str = "low"  # low, medium, high
    provenance: dict[str, Any] | None = None


# ──────────────────────────────────────────────
# Incoming Event Payloads (consumed by Agent-01)
# ──────────────────────────────────────────────


class ForecastDemandPayload(BaseModel):
    """Demand forecast from Agent-06 (Predictive Analytics) for BOM requirements."""

    forecast_id: str
    product_line: str
    material_requirements: dict[str, float]  # material_id → quantity required
    forecast_month: str  # "2026-06"
    confidence_interval: dict[str, float]  # lower, upper
    mape: float | None = None
    scenario: str = "baseline"


class InventorySnapshotPayload(BaseModel):
    """Current inventory levels from Agent-03 (Inventory & Warehousing)."""

    material_id: str
    material_name: str
    current_stock: float
    unit: str
    safety_stock: float
    reorder_point: float
    projected_stock_out_date: str | None = None
    warehouse_location: str
    lot_numbers: list[str] = []


class OrchestratorCommand(BaseModel):
    """Governance commands from Agent-09 (Orchestrator)."""

    command_type: Literal["rollback", "pause", "resume", "reconfigure", "circuit_breaker_status"]
    target_agent: str = "agent-01"
    parameters: dict[str, Any] = {}
    reason: str
    issued_by: str = "agent-09"
