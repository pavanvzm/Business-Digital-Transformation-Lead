"""Decision optimizer for procurement operations.

Handles:
  1. Purchase Order (PO) recommendation — quantity, vendor, delivery date
  2. Vendor selection — rank candidates by score, risk, and cost
  3. Alternative sourcing analysis — identify backup suppliers
  4. Minimum order quantity (MOQ) and lot-size optimization
  5. HITL threshold checks

All decisions include confidence scores, reasoning, and business impact estimates.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import numpy as np

from src.scoring.vendor_scorer import VendorScorer

logger = logging.getLogger(__name__)


@dataclass
class PurchaseOrderRecommendation:
    """A purchase order recommendation with full decision trace."""

    po_id: str = field(default_factory=lambda: f"PO-{uuid4().hex[:8].upper()}")
    vendor_id: str = ""
    vendor_name: str = ""
    material_id: str = ""
    material_name: str = ""
    quantity: float = 0.0
    unit: str = "kg"
    unit_price: float = 0.0
    total_value: float = 0.0
    recommended_delivery_date: str = ""
    confidence: float = 0.85
    reasoning: str = ""
    alternatives: list[str] = field(default_factory=list)
    hitl_required: bool = False
    hitl_reason: str | None = None
    business_impact: dict[str, Any] | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class SourcingAnalysis:
    """Alternative sourcing analysis result."""

    material_id: str
    material_name: str
    primary_vendor: dict[str, Any]
    alternatives: list[dict[str, Any]]
    recommendation: str
    estimated_savings: float | None = None
    switching_risk: str = "low"
    confidence: float = 0.75
    hitl_required: bool = False


class DecisionOptimizer:
    """Optimizes procurement decisions: PO recommendations, vendor selection, sourcing analysis.

    Decision framework:
      1. Gather inputs (demand, inventory, price, vendor scores)
      2. Apply business rules (MOQ, lead time, HITL thresholds)
      3. Optimize (quantity, timing, vendor selection)
      4. Validate (confidence check, constraint satisfaction)
      5. Recommend (with reasoning and alternatives)
    """

    def __init__(
        self,
        scorer: VendorScorer,
        hitl_po_threshold_usd: float = 500_000.0,
        hitl_sole_source_threshold: bool = True,
    ) -> None:
        self._scorer = scorer
        self._hitl_po_threshold = hitl_po_threshold_usd
        self._hitl_sole_source = hitl_sole_source_threshold

    def recommend_purchase_order(
        self,
        material_id: str,
        material_name: str,
        current_stock: float,
        safety_stock: float,
        reorder_point: float,
        forecast_demand: float,
        unit_price: float,
        unit: str = "kg",
        lead_time_days: int = 14,
        min_order_quantity: float | None = None,
        vendor_scores: list[dict[str, Any]] | None = None,
        alternative_sources: list[dict[str, Any]] | None = None,
    ) -> PurchaseOrderRecommendation:
        """Generate a purchase order recommendation with optimization.

        Args:
            material_id: Raw material identifier.
            material_name: Human-readable material name.
            current_stock: Current inventory level.
            safety_stock: Minimum safety stock level.
            reorder_point: Reorder point threshold.
            forecast_demand: Projected demand for the planning period.
            unit_price: Current unit price from best vendor.
            unit: Unit of measure.
            lead_time_days: Supplier lead time in days.
            min_order_quantity: Minimum order quantity constraint.
            vendor_scores: Optional list of vendor scorecards for multi-vendor selection.
            alternative_sources: Optional list of alternative vendor sources.

        Returns:
            PurchaseOrderRecommendation with full decision trace.
        """
        # ── Step 1: Compute optimal order quantity ──
        stock_deficit = max(0.0, reorder_point - current_stock)
        demand_coverage = forecast_demand + safety_stock
        total_needed = stock_deficit + demand_coverage

        # Economic Order Quantity (EOQ) approximation
        # Using the Harris-Wilson formula: EOQ = sqrt(2 * D * S / H)
        # Where D = annual demand, S = ordering cost (~$150), H = holding cost (20% of unit price)
        annual_demand = forecast_demand * 12  # extrapolate to annual
        ordering_cost = 150.0  # fixed ordering cost per PO
        holding_cost = unit_price * 0.20  # 20% holding cost
        if holding_cost > 0:
            eoq = np.sqrt(2 * annual_demand * ordering_cost / holding_cost)
        else:
            eoq = total_needed

        final_quantity = max(total_needed, eoq)

        # Apply MOQ constraint
        if min_order_quantity and min_order_quantity > 0:
            final_quantity = max(final_quantity, min_order_quantity)

        # Round up to nearest whole unit
        final_quantity = np.ceil(final_quantity)

        # ── Step 2: Compute delivery date ──
        delivery_date = datetime.now(timezone.utc) + timedelta(days=lead_time_days)
        recommended_delivery = delivery_date.strftime("%Y-%m-%d")

        # ── Step 3: Vendor selection ──
        best_vendor_id = "VENDOR-DEFAULT"
        best_vendor_name = "Primary Supplier"
        best_price = unit_price
        alternatives: list[str] = []

        if vendor_scores and len(vendor_scores) > 0:
            sorted_vendors = sorted(vendor_scores, key=lambda v: v.get("overall_score", 0), reverse=True)
            best_vendor = sorted_vendors[0]
            best_vendor_id = best_vendor.get("vendor_id", best_vendor_id)
            best_vendor_name = best_vendor.get("vendor_name", best_vendor_name)
            best_price = best_vendor.get("price", unit_price)
            alternatives = [
                f"{v.get('vendor_name', 'Unknown')} ({v.get('overall_score', 0)}/100)"
                for v in sorted_vendors[1:4]
            ]
        elif alternative_sources:
            alternatives = [
                f"{a.get('vendor_name', 'Unknown')} (${a.get('estimated_unit_price', 0):.2f}/unit)"
                for a in alternative_sources[:3]
            ]

        # ── Step 4: Compute total value ──
        total_value = round(final_quantity * best_price, 2)

        # ── Step 5: Check HITL thresholds ──
        hitl_required = False
        hitl_reason = None

        if total_value > self._hitl_po_threshold:
            hitl_required = True
            hitl_reason = f"PO value ${total_value:,.2f} exceeds HITL threshold of ${self._hitl_po_threshold:,.2f}"

        # Sole source check
        if self._hitl_sole_source and not vendor_scores and not alternative_sources:
            sole_source = len(alternatives) == 0 and alternative_sources is None
            if sole_source:
                hitl_required = True
                hitl_reason = (
                    f"Sole-source procurement for {material_name} — "
                    f"no alternative vendors available"
                )

        # ── Step 6: Compute confidence ──
        confidence = self._compute_confidence(
            has_vendor_scores=vendor_scores is not None and len(vendor_scores) > 0,
            has_alternatives=alternative_sources is not None and len(alternative_sources) > 0,
            has_forecast=forecast_demand > 0,
            has_price=unit_price > 0,
        )

        # ── Step 7: Build reasoning ──
        reasoning = (
            f"Optimal PO for {material_name}: {final_quantity:.0f} {unit} "
            f"at ${best_price:.2f}/{unit} (${total_value:,.2f} total). "
            f"Stock={current_stock:.0f} {unit}, reorder_point={reorder_point:.0f} {unit}, "
            f"forecast_demand={forecast_demand:.0f} {unit}. "
            f"EOQ approximation: {eoq:.0f} {unit}. "
            f"Delivery by {recommended_delivery} ({lead_time_days} day lead time)."
        )

        if hitl_required:
            reasoning += f" HITL REQUIRED: {hitl_reason}"

        # Estimate business impact
        business_impact = self._estimate_business_impact(
            total_value, current_stock, safety_stock, forecast_demand, unit_price
        )

        return PurchaseOrderRecommendation(
            vendor_id=best_vendor_id,
            vendor_name=best_vendor_name,
            material_id=material_id,
            material_name=material_name,
            quantity=float(final_quantity),
            unit=unit,
            unit_price=best_price,
            total_value=total_value,
            recommended_delivery_date=recommended_delivery,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=alternatives,
            hitl_required=hitl_required,
            hitl_reason=hitl_reason,
            business_impact=business_impact,
        )

    def analyze_sourcing_options(
        self,
        material_id: str,
        material_name: str,
        primary_vendor: dict[str, Any],
        candidate_vendors: list[dict[str, Any]],
    ) -> SourcingAnalysis:
        """Analyze alternative sourcing options for a material.

        Args:
            material_id: Raw material identifier.
            material_name: Human-readable material name.
            primary_vendor: Current primary vendor details.
            candidate_vendors: List of alternative vendor candidates with scores.

        Returns:
            SourcingAnalysis with ranked alternatives and switching recommendations.
        """
        if not candidate_vendors:
            return SourcingAnalysis(
                material_id=material_id,
                material_name=material_name,
                primary_vendor=primary_vendor,
                alternatives=[],
                recommendation=(
                    f"No alternative sources found for {material_name}. "
                    "Sole-source risk identified — recommend supplier diversification initiative."
                ),
                switching_risk="high",
                confidence=0.3,
                hitl_required=True,
            )

        # Rank candidates by composite score (price + quality + risk)
        scored_candidates: list[tuple[dict[str, Any], float]] = []
        for vendor in candidate_vendors:
            price = vendor.get("estimated_unit_price", 0.0)
            quality = vendor.get("quality_rating", 50.0)
            lead_time = vendor.get("lead_time_days", 30)

            # Composite score: lower price + higher quality + shorter lead time = better
            price_score = max(0, 100 - (price / primary_vendor.get("estimated_unit_price", price) * 50))
            quality_score = quality
            lead_time_score = max(0, 100 - (lead_time / 60 * 100))
            composite = price_score * 0.4 + quality_score * 0.4 + lead_time_score * 0.2

            scored_candidates.append((vendor, round(composite, 1)))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        alternatives_formatted: list[dict[str, Any]] = []
        for vendor, score in scored_candidates:
            alternatives_formatted.append({
                "vendor_id": vendor.get("vendor_id", ""),
                "vendor_name": vendor.get("vendor_name", "Unknown"),
                "estimated_unit_price": vendor.get("estimated_unit_price", 0.0),
                "lead_time_days": vendor.get("lead_time_days", 0),
                "quality_rating": vendor.get("quality_rating"),
                "composite_score": score,
            })

        # Determine switching risk
        best_alternative = scored_candidates[0][0] if scored_candidates else None
        switching_risk = "low"
        estimated_savings = None

        if best_alternative:
            primary_price = primary_vendor.get("estimated_unit_price", 0.0)
            alt_price = best_alternative.get("estimated_unit_price", 0.0)
            if primary_price > 0:
                savings_pct = (primary_price - alt_price) / primary_price * 100
                if savings_pct > 0:
                    estimated_savings = savings_pct
                    switching_risk = "low" if savings_pct > 5 else "medium"

            # Higher lead time increases switching risk
            alt_lead_time = best_alternative.get("lead_time_days", 30)
            primary_lead_time = primary_vendor.get("lead_time_days", 14)
            if alt_lead_time > primary_lead_time * 1.5:
                switching_risk = "medium"

        # Check if HITL is required for sole-source situations
        # Per blueprint: HITL required when there are ZERO alternatives (true sole-source)
        # Having 1+ alternatives means there IS a viable back-up, so no HITL needed
        hitl_required = len(scored_candidates) == 0

        if scored_candidates and best_alternative:
            recommendation = (
                f"Top alternative: {best_alternative.get('vendor_name', 'Unknown')} "
                f"(composite score: {scored_candidates[0][1]:.1f})"
            )
            if estimated_savings:
                savings_amount = primary_vendor.get("estimated_unit_price", 0) - best_alternative.get("estimated_unit_price", 0)
                recommendation += f". Estimated savings: ${savings_amount:.2f}/unit ({estimated_savings:.1f}%)"
            if switching_risk != "low":
                recommendation += f". Switching risk: {switching_risk} — recommend phased transition."
        else:
            recommendation = "No viable alternative sources available."

        confidence = 0.5 + (0.05 * min(len(scored_candidates), 5))

        return SourcingAnalysis(
            material_id=material_id,
            material_name=material_name,
            primary_vendor=primary_vendor,
            alternatives=alternatives_formatted,
            recommendation=recommendation,
            estimated_savings=estimated_savings,
            switching_risk=switching_risk,
            confidence=round(min(confidence, 0.95), 2),
            hitl_required=hitl_required,
        )

    def rank_vendors(
        self,
        vendors: list[dict[str, Any]],
        material_category: str = "general",
    ) -> list[dict[str, Any]]:
        """Rank vendors by composite score for a procurement decision.

        Args:
            vendors: List of vendor dicts with 'vendor_id', 'vendor_name', 'overall_score', 'price'.
            material_category: Material category for weight profile.

        Returns:
            Ranked list of vendors with selection recommendation.
        """
        ranked = sorted(vendors, key=lambda v: v.get("overall_score", 0), reverse=True)

        results: list[dict[str, Any]] = []
        for i, vendor in enumerate(ranked):
            position = i + 1
            score = vendor.get("overall_score", 0)

            if position == 1:
                recommendation = "RECOMMENDED — highest score"
            elif score >= 60:
                recommendation = "Qualified alternative"
            else:
                recommendation = "Below threshold — not recommended"

            if score < 60:
                recommendation += " | HITL required"

            results.append({
                "rank": position,
                "vendor_id": vendor.get("vendor_id"),
                "vendor_name": vendor.get("vendor_name"),
                "overall_score": score,
                "price": vendor.get("price"),
                "recommendation": recommendation,
            })

        return results

    def _compute_confidence(
        self,
        has_vendor_scores: bool,
        has_alternatives: bool,
        has_forecast: bool,
        has_price: bool,
    ) -> float:
        """Compute decision confidence based on data availability."""
        base = 0.7
        if has_vendor_scores:
            base += 0.1
        if has_alternatives:
            base += 0.05
        if has_forecast:
            base += 0.1
        if has_price:
            base += 0.05
        return round(min(base, 0.99), 2)

    def _estimate_business_impact(
        self,
        total_value: float,
        current_stock: float,
        safety_stock: float,
        forecast_demand: float,
        unit_price: float,
    ) -> dict[str, Any]:
        """Estimate business impact of the PO recommendation."""
        stockout_risk = "low"
        if current_stock <= safety_stock * 1.2:
            stockout_risk = "high"
        elif current_stock <= safety_stock * 2:
            stockout_risk = "medium"

        # Estimate cost of stockout (lost production revenue approximation)
        # Using 3x margin on material cost as rough estimate
        stockout_cost = forecast_demand * unit_price * 3 if current_stock < forecast_demand else 0.0

        # Working capital impact
        holding_days = 30  # average days in inventory
        working_capital_impact = total_value * (holding_days / 365) * 0.05  # 5% cost of capital

        return {
            "total_value_usd": total_value,
            "stockout_risk": stockout_risk,
            "estimated_stockout_cost_usd": round(stockout_cost, 2),
            "working_capital_impact_usd": round(working_capital_impact, 2),
            "days_of_cover": round(current_stock / max(forecast_demand / 30.0, 0.01), 1),
        }
