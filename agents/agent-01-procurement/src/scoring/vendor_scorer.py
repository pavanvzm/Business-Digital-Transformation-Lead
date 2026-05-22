"""Vendor scoring engine with 15 configurable metrics, category-specific weight profiles,
trend detection, and risk flagging.

Follows the scoring specification from the Agent Responsibility Matrix:
  - 15 weighted metrics across price, quality, delivery, ESG, financial health, etc.
  - Category-specific weight profiles (critical raw materials, commodity, packaging)
  - Minimum acceptable score: 60/100, critical threshold: 70/100
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Literal

import numpy as np

logger = logging.getLogger(__name__)


class MaterialCategory(str, Enum):
    CRITICAL_RAW = "critical_raw_materials"
    COMMODITY = "commodity_materials"
    PACKAGING = "packaging"
    GENERAL = "general"


@dataclass
class VendorMetric:
    """Individual scoring metric for a vendor."""

    name: str
    score: float  # 0-100
    weight: float  # 0.0-1.0 (weights sum to 1.0 across all metrics)
    data_source: str
    notes: str | None = None
    trend: Literal["improving", "stable", "declining"] = "stable"


@dataclass
class VendorScorecard:
    """Complete vendor scorecard with 15 metrics and composite score."""

    vendor_id: str
    vendor_name: str
    period: str  # "2026-Q2"
    overall_score: float  # 0-100
    metrics: list[VendorMetric]
    category: MaterialCategory = MaterialCategory.GENERAL
    previous_overall_score: float | None = None
    trend: Literal["improving", "stable", "declining"] = "stable"
    risk_flags: list[str] = field(default_factory=list)
    confidence: float = 0.85
    scored_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class VendorScorer:
    """Scoring engine that evaluates vendors across 15 weighted metrics.

    Weight profiles are configurable per material category. The engine applies
    quality gates, trend analysis, and automatic risk flagging.
    """

    # Default metric definitions: (name, default_weight, data_source)
    METRIC_DEFINITIONS: list[tuple[str, float, str]] = [
        ("Price Competitiveness", 0.25, "market_prices"),
        ("Quality Rating", 0.20, "erp_quality"),
        ("On-Time Delivery", 0.15, "erp_po_data"),
        ("ESG Score", 0.10, "esg_api"),
        ("Financial Health", 0.10, "dun_bradstreet"),
        ("Innovation Index", 0.05, "patent_analysis"),
        ("Compliance Rating", 0.05, "compliance_db"),
        ("Relationship Tenure", 0.05, "erp_vendor_master"),
        ("Geographic Diversity", 0.05, "erp_vendor_master"),
    ]

    # Category-specific weight overrides
    CATEGORY_WEIGHTS: dict[MaterialCategory, dict[str, float]] = {
        MaterialCategory.CRITICAL_RAW: {
            "Price Competitiveness": 0.15,
            "Quality Rating": 0.30,
            "On-Time Delivery": 0.25,
            "ESG Score": 0.15,
            "Financial Health": 0.05,
            "Innovation Index": 0.02,
            "Compliance Rating": 0.03,
            "Relationship Tenure": 0.03,
            "Geographic Diversity": 0.02,
        },
        MaterialCategory.COMMODITY: {
            "Price Competitiveness": 0.40,
            "Quality Rating": 0.15,
            "On-Time Delivery": 0.15,
            "ESG Score": 0.10,
            "Financial Health": 0.05,
            "Innovation Index": 0.02,
            "Compliance Rating": 0.03,
            "Relationship Tenure": 0.05,
            "Geographic Diversity": 0.05,
        },
        MaterialCategory.PACKAGING: {
            "Price Competitiveness": 0.30,
            "Quality Rating": 0.15,
            "On-Time Delivery": 0.10,
            "ESG Score": 0.25,
            "Financial Health": 0.05,
            "Innovation Index": 0.02,
            "Compliance Rating": 0.03,
            "Relationship Tenure": 0.05,
            "Geographic Diversity": 0.05,
        },
    }

    def __init__(self, min_acceptable_score: float = 60.0, quality_critical: float = 70.0) -> None:
        self._min_acceptable = min_acceptable_score
        self._quality_critical = quality_critical

    def compute_scorecard(
        self,
        vendor_id: str,
        vendor_name: str,
        metric_scores: dict[str, float],
        category: MaterialCategory = MaterialCategory.GENERAL,
        previous_score: float | None = None,
        metric_notes: dict[str, str] | None = None,
    ) -> VendorScorecard:
        """Compute a complete vendor scorecard from raw metric scores.

        Args:
            vendor_id: Unique vendor identifier.
            vendor_name: Vendor display name.
            metric_scores: Dict mapping metric name → score (0-100).
            category: Material category for weight profile selection.
            previous_score: Previous period overall score for trend detection.
            metric_notes: Optional notes per metric.

        Returns:
            VendorScorecard with composite score, metric breakdown, trends, and risk flags.
        """
        # Get weights for the category
        weights = self._get_weights(category)

        # Build metric objects with computed weighted scores
        metrics: list[VendorMetric] = []
        total_weighted_score = 0.0
        total_weight = 0.0

        for metric_name, default_weight in [(m[0], m[1]) for m in self.METRIC_DEFINITIONS]:
            score = metric_scores.get(metric_name)
            if score is None:
                logger.warning("Missing metric score", vendor_id=vendor_id, metric=metric_name)
                continue

            weight = weights.get(metric_name, default_weight)
            total_weighted_score += score * weight
            total_weight += weight

            metrics.append(VendorMetric(
                name=metric_name,
                score=score,
                weight=weight,
                data_source=dict(self.METRIC_DEFINITIONS).get(metric_name, "unknown"),
                notes=metric_notes.get(metric_name) if metric_notes else None,
            ))

        # Normalize if weights don't sum to 1.0
        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
        overall_score = round(min(max(overall_score, 0.0), 100.0), 1)

        # Detect trend
        trend: Literal["improving", "stable", "declining"] = "stable"
        if previous_score is not None:
            diff = overall_score - previous_score
            if diff > 3.0:
                trend = "improving"
            elif diff < -3.0:
                trend = "declining"
            else:
                trend = "stable"

        # Generate risk flags
        risk_flags = self._detect_risks(overall_score, metrics)

        return VendorScorecard(
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            period=self._current_period(),
            overall_score=overall_score,
            metrics=metrics,
            category=category,
            previous_overall_score=previous_score,
            trend=trend,
            risk_flags=risk_flags,
        )

    def score_vendor_selection(
        self,
        candidate_vendors: list[VendorScorecard],
    ) -> list[tuple[VendorScorecard, str]]:
        """Score and rank multiple vendors for selection.

        Returns list of (scorecard, recommendation) tuples sorted by score descending.
        """
        ranked = sorted(candidate_vendors, key=lambda v: v.overall_score, reverse=True)

        results: list[tuple[VendorScorecard, str]] = []
        for i, vendor in enumerate(ranked):
            if i == 0 and vendor.overall_score >= self._min_acceptable:
                recommendation = self._generate_recommendation(vendor, ranked[1] if len(ranked) > 1 else None)
            else:
                recommendation = self._generate_position_recommendation(vendor, i)
            results.append((vendor, recommendation))

        return results

    def _get_weights(self, category: MaterialCategory) -> dict[str, float]:
        """Get weight profile for a material category."""
        return self.CATEGORY_WEIGHTS.get(category, {
            m[0]: m[1] for m in self.METRIC_DEFINITIONS
        })

    def _detect_risks(self, overall_score: float, metrics: list[VendorMetric]) -> list[str]:
        """Detect risk flags from scorecard."""
        flags: list[str] = []

        if overall_score < self._min_acceptable:
            flags.append(f"Below minimum acceptable score ({self._min_acceptable})")
        if overall_score < self._quality_critical:
            flags.append(f"CRITICAL: Score below quality threshold ({self._quality_critical}) → HITL required")

        for metric in metrics:
            if metric.score < 40.0:
                flags.append(f"Low {metric.name} score ({metric.score}/100)")
            if metric.trend == "declining":
                flags.append(f"{metric.name} trend is declining")

        if len(flags) > 3:
            flags.append("Multiple risk factors detected — recommend thorough review")

        return flags

    def _generate_recommendation(
        self,
        top_vendor: VendorScorecard,
        runner_up: VendorScorecard | None,
    ) -> str:
        """Generate selection recommendation for top vendor."""
        parts: list[str] = [
            f"Recommended: {top_vendor.vendor_name} (score: {top_vendor.overall_score}/100)"
        ]

        if runner_up:
            score_diff = top_vendor.overall_score - runner_up.overall_score
            if score_diff > 15.0:
                parts.append(f"Clear leader — {score_diff:.1f} points ahead of {runner_up.vendor_name}")
            elif score_diff < 5.0:
                parts.append(f"Tight race — only {score_diff:.1f} points ahead of {runner_up.vendor_name}")

        if top_vendor.risk_flags:
            parts.append(f"Risk flags: {'; '.join(top_vendor.risk_flags[:2])}")

        return " | ".join(parts)

    def _generate_position_recommendation(self, vendor: VendorScorecard, position: int) -> str:
        """Generate recommendation for non-top vendors."""
        if vendor.overall_score >= self._min_acceptable:
            return f"Qualified alternative (position {position + 1}) — score: {vendor.overall_score}/100"
        else:
            return (
                f"Below minimum threshold (position {position + 1}) — score: {vendor.overall_score}/100. "
                "Consider requalification or exclusion."
            )

    @staticmethod
    def _current_period() -> str:
        """Get current quarterly period string."""
        now = datetime.now(timezone.utc)
        quarter = (now.month - 1) // 3 + 1
        return f"{now.year}-Q{quarter}"

    @staticmethod
    def compute_price_score(
        quoted_price: float,
        market_avg_price: float,
        market_std: float = 0.0,
    ) -> float:
        """Compute price competitiveness score (0-100).

        Score based on how quoted price compares to market average.
        Lower is better (cheaper relative to market).
        """
        if market_avg_price <= 0:
            return 50.0  # neutral score if no market data

        deviation = (quoted_price - market_avg_price) / market_avg_price * 100

        if deviation <= -10.0:  # 10%+ below market
            return 100.0
        elif deviation <= -5.0:  # 5-10% below
            return 90.0
        elif deviation <= 0.0:  # at or slightly below
            return 80.0
        elif deviation <= 5.0:  # up to 5% above
            return 60.0
        elif deviation <= 10.0:  # 5-10% above
            return 40.0
        elif deviation <= 20.0:  # 10-20% above
            return 20.0
        else:
            return 0.0  # 20%+ above market

    @staticmethod
    def compute_quality_score(defect_ppm: float) -> float:
        """Convert defect PPM to a 0-100 quality score."""
        if defect_ppm <= 0:
            return 100.0
        # Target: <1,000 PPM (99.9% yield) = 100, >100,000 PPM = 0
        score = 100.0 * (1.0 - np.log10(defect_ppm + 1) / 5.0)
        return round(max(0.0, min(100.0, score)), 1)

    @staticmethod
    def compute_delivery_score(otif_pct: float) -> float:
        """Convert OTIF percentage to a 0-100 delivery score."""
        if otif_pct >= 100.0:
            return 100.0
        elif otif_pct >= 98.0:
            return 95.0
        elif otif_pct >= 95.0:
            return 80.0
        elif otif_pct >= 90.0:
            return 60.0
        elif otif_pct >= 80.0:
            return 40.0
        else:
            return max(0.0, otif_pct)  # below 80% — score equals OTIF
