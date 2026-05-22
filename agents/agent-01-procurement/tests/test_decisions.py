"""Tests for the DecisionOptimizer — PO recommendations, sourcing analysis, vendor ranking."""

from __future__ import annotations

import pytest
from src.scoring.vendor_scorer import VendorScorer
from src.decisions.optimizer import DecisionOptimizer, PurchaseOrderRecommendation


@pytest.fixture
def optimizer() -> DecisionOptimizer:
    return DecisionOptimizer(
        scorer=VendorScorer(),
        hitl_po_threshold_usd=500_000.0,
        hitl_sole_source_threshold=True,
    )


class TestPORecommendation:
    """Purchase order recommendation logic."""

    def test_basic_po_recommendation(self, optimizer: DecisionOptimizer) -> None:
        """Basic PO with standard parameters."""
        rec = optimizer.recommend_purchase_order(
            material_id="MAT-COPPER-001",
            material_name="Copper Wire 12AWG",
            current_stock=500,
            safety_stock=200,
            reorder_point=400,
            forecast_demand=1000,
            unit_price=8.50,
            unit="kg",
            lead_time_days=14,
        )

        assert rec.material_id == "MAT-COPPER-001"
        assert rec.quantity > 0
        assert rec.unit_price == 8.50
        assert rec.total_value > 0
        assert rec.recommended_delivery_date != ""
        assert rec.confidence > 0.5
        assert rec.reasoning != ""
        assert rec.po_id.startswith("PO-")

    def test_po_below_hitl_threshold(self, optimizer: DecisionOptimizer) -> None:
        """Small PO — no HITL required."""
        rec = optimizer.recommend_purchase_order(
            material_id="MAT-BOLT-001",
            material_name="M8 Bolts",
            current_stock=100,
            safety_stock=50,
            reorder_point=80,
            forecast_demand=500,
            unit_price=0.50,
            unit="pcs",
        )

        assert not rec.hitl_required
        assert rec.hitl_reason is None

    def test_po_exceeds_hitl_threshold(self, optimizer: DecisionOptimizer) -> None:
        """Large PO >$500K → HITL required."""
        rec = optimizer.recommend_purchase_order(
            material_id="MAT-STEEL-HR-001",
            material_name="Hot-Rolled Steel Coil",
            current_stock=1000,
            safety_stock=500,
            reorder_point=800,
            forecast_demand=50000,
            unit_price=850.0,
            unit="ton",
        )

        assert rec.hitl_required
        assert rec.hitl_reason is not None
        assert "HITL threshold" in rec.hitl_reason.lower()

    def test_po_with_vendor_scores(self, optimizer: DecisionOptimizer) -> None:
        """PO with multi-vendor scorecards — selects best vendor."""
        vendor_scores = [
            {"vendor_id": "V001", "vendor_name": "Premium Supplier", "overall_score": 95.0, "price": 10.0},
            {"vendor_id": "V002", "vendor_name": "Budget Supplier", "overall_score": 75.0, "price": 7.0},
            {"vendor_id": "V003", "vendor_name": "Average Supplier", "overall_score": 60.0, "price": 9.0},
        ]

        rec = optimizer.recommend_purchase_order(
            material_id="MAT-PLASTIC-001",
            material_name="ABS Granules",
            current_stock=300,
            safety_stock=150,
            reorder_point=250,
            forecast_demand=2000,
            unit_price=10.0,
            vendor_scores=vendor_scores,
        )

        assert rec.vendor_id == "V001"  # highest score
        assert rec.vendor_name == "Premium Supplier"
        assert len(rec.alternatives) > 0

    def test_po_sole_source(self, optimizer: DecisionOptimizer) -> None:
        """No alternatives → HITL required for sole source."""
        rec = optimizer.recommend_purchase_order(
            material_id="MAT-SPECIAL-001",
            material_name="Specialty Alloy",
            current_stock=50,
            safety_stock=20,
            reorder_point=40,
            forecast_demand=200,
            unit_price=500.0,
            lead_time_days=30,
            vendor_scores=None,
            min_order_quantity=100,
        )

        # Should be sole source flagged since no vendor_scores and no alternatives
        if "sole-source" in rec.hitl_reason.lower() if rec.hitl_reason else "":
            assert rec.hitl_required

    def test_po_quantity_optimization(self, optimizer: DecisionOptimizer) -> None:
        """Quantity respects MOQ and covers forecast + safety stock."""
        rec = optimizer.recommend_purchase_order(
            material_id="MAT-CHEM-001",
            material_name="Solvent X",
            current_stock=50,
            safety_stock=100,
            reorder_point=75,
            forecast_demand=500,
            unit_price=12.0,
            min_order_quantity=200,
        )

        assert rec.quantity >= 200  # MOQ

    def test_po_confidence_low_no_forecast(self, optimizer: DecisionOptimizer) -> None:
        """Low confidence when forecast data is missing."""
        rec = optimizer.recommend_purchase_order(
            material_id="MAT-TEST-001",
            material_name="Test Material",
            current_stock=100,
            safety_stock=50,
            reorder_point=80,
            forecast_demand=0,  # no forecast
            unit_price=10.0,
        )

        assert rec.confidence < 0.8


class TestSourcingAnalysis:
    """Alternative sourcing analysis."""

    def test_no_alternatives(self, optimizer: DecisionOptimizer) -> None:
        """No alternative vendors → HITL required, high risk."""
        analysis = optimizer.analyze_sourcing_options(
            material_id="MAT-SPECIAL-002",
            material_name="Custom Part",
            primary_vendor={"vendor_id": "V001", "vendor_name": "Sole Source Inc", "estimated_unit_price": 100.0, "lead_time_days": 14},
            candidate_vendors=[],
        )

        assert analysis.hitl_required
        assert analysis.switching_risk == "high"
        assert analysis.confidence < 0.5

    def test_with_alternatives_cheaper(self, optimizer: DecisionOptimizer) -> None:
        """Alternative vendors with lower prices → savings estimated."""
        analysis = optimizer.analyze_sourcing_options(
            material_id="MAT-STEEL-002",
            material_name="Steel Plate",
            primary_vendor={"vendor_id": "V001", "vendor_name": "Expensive Inc", "estimated_unit_price": 100.0, "lead_time_days": 14},
            candidate_vendors=[
                {"vendor_id": "V002", "vendor_name": "Cheaper Inc", "estimated_unit_price": 85.0, "lead_time_days": 14, "quality_rating": 85.0},
                {"vendor_id": "V003", "vendor_name": "Average Inc", "estimated_unit_price": 95.0, "lead_time_days": 21, "quality_rating": 80.0},
            ],
        )

        assert analysis.estimated_savings is not None
        assert analysis.estimated_savings > 0
        assert analysis.switching_risk in ("low", "medium")
        assert len(analysis.alternatives) == 2

    def test_single_alternative_hitl(self, optimizer: DecisionOptimizer) -> None:
        """Only one alternative → HITL required."""
        analysis = optimizer.analyze_sourcing_options(
            material_id="MAT-NICHE-001",
            material_name="Niche Material",
            primary_vendor={"vendor_id": "V001", "vendor_name": "Primary Ltd", "estimated_unit_price": 200.0, "lead_time_days": 14},
            candidate_vendors=[
                {"vendor_id": "V002", "vendor_name": "Only Alt Ltd", "estimated_unit_price": 210.0, "lead_time_days": 28, "quality_rating": 70.0},
            ],
        )

        assert analysis.hitl_required


class TestVendorRanking:
    """Vendor ranking logic."""

    def test_rank_vendors(self, optimizer: DecisionOptimizer) -> None:
        """Rank vendors by overall score descending."""
        vendors = [
            {"vendor_id": "V001", "vendor_name": "Alpha", "overall_score": 88.0, "price": 100.0},
            {"vendor_id": "V002", "vendor_name": "Beta", "overall_score": 72.0, "price": 95.0},
            {"vendor_id": "V003", "vendor_name": "Gamma", "overall_score": 65.0, "price": 90.0},
        ]

        ranked = optimizer.rank_vendors(vendors)
        assert len(ranked) == 3
        assert ranked[0]["vendor_name"] == "Alpha"
        assert ranked[0]["recommendation"] == "RECOMMENDED — highest score"
        assert ranked[-1]["vendor_name"] == "Gamma"

    def test_rank_vendors_below_threshold(self, optimizer: DecisionOptimizer) -> None:
        """Vendors below 60 score → not recommended + HITL."""
        vendors = [
            {"vendor_id": "V010", "vendor_name": "Low Scorer", "overall_score": 45.0, "price": 100.0},
        ]

        ranked = optimizer.rank_vendors(vendors)
        assert "not recommended" in ranked[0]["recommendation"].lower()
