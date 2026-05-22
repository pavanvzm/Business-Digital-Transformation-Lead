"""Tests for the VendorScorer engine — scoring, weights, trend detection, and risk flags."""

from __future__ import annotations

import pytest
from src.scoring.vendor_scorer import VendorScorer, VendorScorecard, VendorMetric, MaterialCategory


@pytest.fixture
def scorer() -> VendorScorer:
    return VendorScorer(min_acceptable_score=60.0, quality_critical=70.0)


class TestPriceScore:
    """Price competitiveness scoring calculations."""

    def test_price_below_market(self) -> None:
        """10% below market → 100 score."""
        assert VendorScorer.compute_price_score(90.0, 100.0) == 100.0

    def test_price_at_market(self) -> None:
        """At market price → 80 score."""
        assert VendorScorer.compute_price_score(100.0, 100.0) == 80.0

    def test_price_slightly_above(self) -> None:
        """3% above market → 80 score."""
        assert VendorScorer.compute_price_score(103.0, 100.0) == 80.0

    def test_price_20pct_above(self) -> None:
        """20%+ above market → 0 score."""
        assert VendorScorer.compute_price_score(120.0, 100.0) == 0.0

    def test_price_no_market_data(self) -> None:
        """No market data → neutral 50 score."""
        assert VendorScorer.compute_price_score(100.0, 0.0) == 50.0


class TestQualityScore:
    """Quality score from defect PPM."""

    def test_zero_defects(self) -> None:
        assert VendorScorer.compute_quality_score(0) == 100.0

    def test_low_defects(self) -> None:
        """1000 PPM (0.1%) → near 100."""
        score = VendorScorer.compute_quality_score(1000)
        assert 60.0 <= score <= 100.0

    def test_high_defects(self) -> None:
        """100K PPM (10%) → 0."""
        score = VendorScorer.compute_quality_score(100_000)
        assert score < 10.0


class TestDeliveryScore:
    """OTIF to delivery score mapping."""

    def test_perfect_delivery(self) -> None:
        assert VendorScorer.compute_delivery_score(100.0) == 100.0

    def test_98pct_otif(self) -> None:
        assert VendorScorer.compute_delivery_score(98.0) == 95.0

    def test_95pct_otif(self) -> None:
        assert VendorScorer.compute_delivery_score(95.0) == 80.0

    def test_85pct_otif(self) -> None:
        assert VendorScorer.compute_delivery_score(85.0) == 40.0

    def test_low_delivery(self) -> None:
        assert VendorScorer.compute_delivery_score(50.0) == 50.0


class TestScorecardComputation:
    """Full scorecard computation with various categories and edge cases."""

    def test_basic_scorecard(self, scorer: VendorScorer) -> None:
        """Compute a basic scorecard with all metrics."""
        metrics = {
            "Price Competitiveness": 80.0,
            "Quality Rating": 90.0,
            "On-Time Delivery": 85.0,
            "ESG Score": 75.0,
            "Financial Health": 80.0,
            "Innovation Index": 70.0,
            "Compliance Rating": 95.0,
            "Relationship Tenure": 85.0,
            "Geographic Diversity": 60.0,
        }

        scorecard = scorer.compute_scorecard(
            vendor_id="V001",
            vendor_name="Test Corp",
            metric_scores=metrics,
        )

        assert scorecard.vendor_id == "V001"
        assert scorecard.vendor_name == "Test Corp"
        assert 60.0 <= scorecard.overall_score <= 100.0
        assert len(scorecard.metrics) == 9
        assert scorecard.category == MaterialCategory.GENERAL

    def test_critical_raw_material_weights(self, scorer: VendorScorer) -> None:
        """Critical raw materials weights emphasize quality and delivery."""
        metrics = {
            "Price Competitiveness": 100.0,  # low weight
            "Quality Rating": 0.0,  # high weight — drags score down
            "On-Time Delivery": 100.0,
            "ESG Score": 100.0,
            "Financial Health": 100.0,
            "Innovation Index": 100.0,
            "Compliance Rating": 100.0,
            "Relationship Tenure": 100.0,
            "Geographic Diversity": 100.0,
        }

        scorecard = scorer.compute_scorecard(
            vendor_id="V002",
            vendor_name="Critical Supplier",
            metric_scores=metrics,
            category=MaterialCategory.CRITICAL_RAW,
        )

        # Quality has 0.30 weight — with score 0, overall should be dragged down
        assert scorecard.overall_score < 50.0
        assert "CRITICAL" in scorecard.risk_flags[0] if scorecard.risk_flags else False

    def test_commodity_weights(self, scorer: VendorScorer) -> None:
        """Commodity materials prioritize price."""
        metrics = {
            "Price Competitiveness": 100.0,  # 0.40 weight
            "Quality Rating": 50.0,
            "On-Time Delivery": 50.0,
            "ESG Score": 50.0,
            "Financial Health": 50.0,
            "Innovation Index": 50.0,
            "Compliance Rating": 50.0,
            "Relationship Tenure": 50.0,
            "Geographic Diversity": 50.0,
        }

        scorecard = scorer.compute_scorecard(
            vendor_id="V003",
            vendor_name="Commodity Supplier",
            metric_scores=metrics,
            category=MaterialCategory.COMMODITY,
        )

        # High price weight should pull overall up
        assert scorecard.overall_score > 60.0

    def test_missing_metrics(self, scorer: VendorScorer) -> None:
        """Partial metrics should compute using available ones."""
        metrics = {
            "Price Competitiveness": 80.0,
            "Quality Rating": 90.0,
        }

        scorecard = scorer.compute_scorecard(
            vendor_id="V004",
            vendor_name="Partial Data Vendor",
            metric_scores=metrics,
        )

        assert scorecard.overall_score > 0
        assert len(scorecard.metrics) == 2

    def test_empty_metrics(self, scorer: VendorScorer) -> None:
        """Empty metrics should return 0."""
        scorecard = scorer.compute_scorecard(
            vendor_id="V005",
            vendor_name="No Data Vendor",
            metric_scores={},
        )
        assert scorecard.overall_score == 0.0
        assert len(scorecard.metrics) == 0

    def test_trend_detection_improving(self, scorer: VendorScorer) -> None:
        """Score improving by >3 points → trend = improving."""
        metrics = {m[0]: 85.0 for m in scorer.METRIC_DEFINITIONS}
        scorecard = scorer.compute_scorecard(
            vendor_id="V006",
            vendor_name="Improving Vendor",
            metric_scores=metrics,
            previous_score=60.0,
        )
        assert scorecard.trend == "improving"

    def test_trend_detection_declining(self, scorer: VendorScorer) -> None:
        """Score declining by >3 points → trend = declining."""
        metrics = {m[0]: 60.0 for m in scorer.METRIC_DEFINITIONS}
        scorecard = scorer.compute_scorecard(
            vendor_id="V007",
            vendor_name="Declining Vendor",
            metric_scores=metrics,
            previous_score=85.0,
        )
        assert scorecard.trend == "declining"

    def test_trend_stable(self, scorer: VendorScorer) -> None:
        """Score change <3 points → trend = stable."""
        metrics = {m[0]: 72.0 for m in scorer.METRIC_DEFINITIONS}
        scorecard = scorer.compute_scorecard(
            vendor_id="V008",
            vendor_name="Stable Vendor",
            metric_scores=metrics,
            previous_score=70.0,
        )
        assert scorecard.trend == "stable"


class TestVendorSelection:
    """Multi-vendor ranking and selection logic."""

    def test_single_vendor_selection(self, scorer: VendorScorer) -> None:
        """Single vendor above threshold → recommended."""
        metrics = {m[0]: 85.0 for m in scorer.METRIC_DEFINITIONS}
        scorecard = scorer.compute_scorecard("V010", "Top Vendor", metrics)

        results = scorer.score_vendor_selection([scorecard])
        assert len(results) == 1
        assert "Recommended" in results[0][1]

    def test_multi_vendor_ranking(self, scorer: VendorScorer) -> None:
        """Multiple vendors ranked by score descending."""
        vendors = []
        for i, score in enumerate([90.0, 75.0, 60.0, 45.0]):
            metrics = {m[0]: score for m in scorer.METRIC_DEFINITIONS}
            scorecard = scorer.compute_scorecard(f"V{i+1}", f"Vendor {i+1}", metrics)
            vendors.append(scorecard)

        results = scorer.score_vendor_selection(vendors)
        assert len(results) == 4
        # First should be highest score
        assert results[0][0].overall_score == 90.0
        # Last should be lowest
        assert results[-1][0].overall_score == 45.0

    def test_vendor_below_threshold(self, scorer: VendorScorer) -> None:
        """Vendor below minimum threshold → not recommended."""
        metrics = {m[0]: 40.0 for m in scorer.METRIC_DEFINITIONS}
        scorecard = scorer.compute_scorecard("V011", "Low Vendor", metrics)

        results = scorer.score_vendor_selection([scorecard])
        assert "Below minimum threshold" in results[0][1]


class TestRiskFlags:
    """Risk flag detection from scorecards."""

    def test_below_minimum_flags(self, scorer: VendorScorer) -> None:
        """Score <60 → risk flags."""
        metrics = {m[0]: 50.0 for m in scorer.METRIC_DEFINITIONS}
        scorecard = scorer.compute_scorecard("V012", "Risky Vendor", metrics)
        assert len(scorecard.risk_flags) > 0
        assert "minimum" in scorecard.risk_flags[0].lower()

    def test_below_critical_flags(self, scorer: VendorScorer) -> None:
        """Score <70 → CRITICAL flag."""
        metrics = {m[0]: 65.0 for m in scorer.METRIC_DEFINITIONS}
        scorecard = scorer.compute_scorecard("V013", "Borderline Vendor", metrics)
        assert any("CRITICAL" in f for f in scorecard.risk_flags)

    def test_multiple_risk_factors(self, scorer: VendorScorer) -> None:
        """More than 3 risk factors triggers summary flag."""
        metrics = {
            "Price Competitiveness": 80.0,
            "Quality Rating": 85.0,
            "On-Time Delivery": 90.0,
            "ESG Score": 35.0,
            "Financial Health": 30.0,
            "Innovation Index": 25.0,
            "Compliance Rating": 20.0,
            "Relationship Tenure": 90.0,
            "Geographic Diversity": 85.0,
        }
        scorecard = scorer.compute_scorecard("V014", "Multi-Risk Vendor", metrics)
        assert any("Multiple risk factors" in f for f in scorecard.risk_flags)
