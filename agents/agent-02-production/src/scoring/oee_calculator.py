"""OEE (Overall Equipment Effectiveness) calculation engine for production lines.

Follows the standard OEE formula:
    OEE = Availability × Performance × Quality

Where:
    Availability  = (Operating Time / Planned Production Time) × 100
    Performance   = (Ideal Cycle Time × Total Units / Operating Time) × 100
    Quality       = (Good Units / Total Units) × 100
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class TrendDirection(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


@dataclass
class OEEComponent:
    """Single OEE component data."""

    name: str
    value_pct: float
    sub_metrics: dict[str, float] = field(default_factory=dict)


@dataclass
class OEEBreakdown:
    """Full OEE breakdown for a production line or shift."""

    production_line: str
    shift_id: str
    period_start: datetime
    period_end: datetime
    availability_pct: float
    performance_pct: float
    quality_pct: float
    oee_pct: float
    is_valid: bool = True
    loss_breakdown: dict[str, float] = field(default_factory=dict)
    components: list[OEEComponent] = field(default_factory=list)
    total_units_produced: int = 0
    total_good_units: int = 0
    total_defective_units: int = 0
    total_downtime_minutes: float = 0.0
    planned_downtime_minutes: float = 0.0
    trend: TrendDirection = TrendDirection.STABLE
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "production_line": self.production_line,
            "shift_id": self.shift_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "availability_pct": round(self.availability_pct, 2),
            "performance_pct": round(self.performance_pct, 2),
            "quality_pct": round(self.quality_pct, 2),
            "oee_pct": round(self.oee_pct, 2),
            "is_valid": self.is_valid,
            "loss_breakdown": self.loss_breakdown,
            "components": [
                {"name": c.name, "value_pct": c.value_pct, "sub_metrics": c.sub_metrics}
                for c in self.components
            ],
            "total_units_produced": self.total_units_produced,
            "total_good_units": self.total_good_units,
            "total_defective_units": self.total_defective_units,
            "total_downtime_minutes": self.total_downtime_minutes,
            "planned_downtime_minutes": self.planned_downtime_minutes,
            "trend": self.trend.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class SPCViolation:
    """Statistical Process Control rule violation."""

    rule_name: str
    machine_id: str
    parameter_name: str
    severity: str  # info, warning, alert, critical
    value: float
    upper_control_limit: float
    lower_control_limit: float
    description: str


class OEECalculator:
    """Calculates OEE and related production metrics.

    Supports:
    - Standard OEE: Availability × Performance × Quality
    - SPC rule checking (6 Nelson rules)
    - Trend analysis over historical windows
    - Bottleneck identification via utilization analysis
    """

    def __init__(
        self,
        availability_target: float = 90.0,
        performance_target: float = 95.0,
        quality_target: float = 99.0,
        history_window: int = 20,  # number of periods for trend analysis
    ) -> None:
        self.availability_target = availability_target
        self.performance_target = performance_target
        self.quality_target = quality_target
        self.history_window = history_window
        self._history: dict[str, list[float]] = {}  # line -> [oee_pct, ...]

    def calculate_oee(
        self,
        production_line: str,
        shift_id: str,
        period_start: datetime,
        period_end: datetime,
        operating_time_minutes: float,
        planned_production_time_minutes: float,
        ideal_cycle_time_seconds: float,
        total_units_produced: int,
        total_good_units: int,
        total_defective_units: int,
        total_downtime_minutes: float,
        planned_downtime_minutes: float,
    ) -> OEEBreakdown:
        """Calculate full OEE breakdown for a production period."""
        # Track validity — any zero/negative fundamental input makes result invalid
        is_valid = True
        if planned_production_time_minutes <= 0:
            is_valid = False
        if operating_time_minutes < 0 or total_downtime_minutes < 0 or planned_downtime_minutes < 0:
            is_valid = False
        if ideal_cycle_time_seconds <= 0:
            is_valid = False
        if total_units_produced < 0 or total_good_units < 0 or total_defective_units < 0:
            is_valid = False
        if total_good_units + total_defective_units > total_units_produced:
            is_valid = False

        # --- Availability ---
        # Availability = Operating Time / Planned Production Time
        if planned_production_time_minutes > 0:
            availability_pct = (
                operating_time_minutes / planned_production_time_minutes
            ) * 100.0
        else:
            availability_pct = 0.0

        # --- Performance ---
        # Performance = (Ideal Cycle Time × Total Units) / Operating Time
        if operating_time_minutes > 0:
            operating_time_seconds = operating_time_minutes * 60.0
            theoretical_throughput = ideal_cycle_time_seconds * total_units_produced
            performance_pct = (
                theoretical_throughput / operating_time_seconds
            ) * 100.0
            # Cap at 100% (can exceed due to running faster than ideal)
            performance_pct = min(performance_pct, 100.0)
        else:
            performance_pct = 0.0

        # --- Quality ---
        # Quality = Good Units / Total Units
        if total_units_produced > 0:
            quality_pct = (
                total_good_units / total_units_produced
            ) * 100.0
        else:
            quality_pct = 100.0  # no production = no defects

        # --- OEE ---
        oee_pct = (availability_pct / 100.0) * (performance_pct / 100.0) * (quality_pct / 100.0) * 100.0

        # --- 6-Loss Breakdown ---
        # Map downtime to the 6 big loss categories
        unplanned_downtime = max(total_downtime_minutes - planned_downtime_minutes, 0.0)
        availability_loss = 100.0 - availability_pct
        speed_loss = 100.0 - performance_pct if performance_pct > 0 else 0.0
        quality_loss = 100.0 - quality_pct

        loss_breakdown = {
            "equipment_failure_loss_pct": max(availability_loss * 0.35, 0.0) if unplanned_downtime > 0 else 0.0,
            "setup_adjustment_loss_pct": max(availability_loss * 0.15, 0.0),
            "idling_minor_stops_loss_pct": max(speed_loss * 0.40, 0.0),
            "reduced_speed_loss_pct": max(speed_loss * 0.35, 0.0),
            "defect_process_loss_pct": max(quality_loss * 0.60, 0.0),
            "reduced_yield_loss_pct": max(quality_loss * 0.40, 0.0),
        }
        # Normalize to actual proportions from the data when possible
        if unplanned_downtime > 0 and total_downtime_minutes > 0:
            # Equipment failure is the dominant unplanned loss
            loss_breakdown["equipment_failure_loss_pct"] = max(
                (unplanned_downtime / max(total_downtime_minutes, 1)) * availability_loss * 0.7, 0.0
            )
            loss_breakdown["setup_adjustment_loss_pct"] = max(
                (planned_downtime_minutes / max(total_downtime_minutes, 1)) * availability_loss * 0.5, 0.0
            )

        # --- Components ---
        availability_metrics = {
            "planned_downtime_minutes": planned_downtime_minutes,
            "unplanned_downtime_minutes": total_downtime_minutes - planned_downtime_minutes,
            "operating_time_minutes": operating_time_minutes,
        }
        performance_metrics = {
            "ideal_cycle_time_seconds": ideal_cycle_time_seconds,
            "actual_avg_cycle_time_seconds": (
                (operating_time_minutes * 60.0) / total_units_produced if total_units_produced > 0 else 0
            ),
            "speed_loss_pct": 100.0 - performance_pct if performance_pct > 0 else 0.0,
        }
        quality_metrics = {
            "first_pass_yield_pct": quality_pct,
            "scrap_rate_pct": (total_defective_units / total_units_produced * 100.0)
            if total_units_produced > 0 else 0.0,
            "rework_rate_pct": 0.0,  # would need separate tracking
        }

        components = [
            OEEComponent(name="availability", value_pct=round(availability_pct, 2), sub_metrics=availability_metrics),
            OEEComponent(name="performance", value_pct=round(performance_pct, 2), sub_metrics=performance_metrics),
            OEEComponent(name="quality", value_pct=round(quality_pct, 2), sub_metrics=quality_metrics),
        ]

        # --- Trend ---
        self._update_history(production_line, oee_pct)
        trend = self._compute_trend(production_line)

        return OEEBreakdown(
            production_line=production_line,
            shift_id=shift_id,
            period_start=period_start,
            period_end=period_end,
            availability_pct=round(availability_pct, 2),
            performance_pct=round(performance_pct, 2),
            quality_pct=round(quality_pct, 2),
            oee_pct=round(oee_pct, 2),
            is_valid=is_valid,
            loss_breakdown={k: round(v, 2) for k, v in loss_breakdown.items()},
            components=components,
            total_units_produced=total_units_produced,
            total_good_units=total_good_units,
            total_defective_units=total_defective_units,
            total_downtime_minutes=total_downtime_minutes,
            planned_downtime_minutes=planned_downtime_minutes,
            trend=trend,
        )

    def check_spc_rules(
        self,
        machine_id: str,
        parameter_name: str,
        values: list[float],
        mean: float | None = None,
        std: float | None = None,
    ) -> list[SPCViolation]:
        """Check Nelson rules for statistical process control.

        Rules implemented:
        - Rule 1: 1 point beyond ±3σ
        - Rule 2: 9 points on same side of center
        - Rule 3: 6 points trending (consistently increasing or decreasing)
        - Rule 4: 14 points alternating up/down
        - Rule 5: 2 of 3 points beyond ±2σ
        - Rule 6: 4 of 5 points beyond ±1σ
        """
        if len(values) < 2:
            return []

        if mean is None:
            mean = float(np.mean(values))
        if std is None:
            std = float(np.std(values, ddof=1))
            if std == 0.0:
                return []  # no variation to detect

        violations: list[SPCViolation] = []
        last_value = values[-1]

        # Rule 1: 1 point beyond ±3σ (Zone A+)
        if abs(last_value - mean) > 3 * std:
            violations.append(SPCViolation(
                rule_name="Rule 1 — 1 point beyond ±3σ",
                machine_id=machine_id,
                parameter_name=parameter_name,
                severity="critical",
                value=last_value,
                upper_control_limit=float(mean + 3 * std),
                lower_control_limit=float(mean - 3 * std),
                description=f"Point {last_value:.2f} is beyond ±3σ from mean {mean:.2f}",
            ))

        # Rule 2: 9 points on same side of center
        if len(values) >= 9:
            last_9 = values[-9:]
            above_count = sum(1 for v in last_9 if v > mean)
            below_count = sum(1 for v in last_9 if v < mean)
            if above_count >= 9:
                violations.append(SPCViolation(
                    rule_name="Rule 2 — 9 points on same side of center (above)",
                    machine_id=machine_id,
                    parameter_name=parameter_name,
                    severity="warning",
                    value=last_value,
                    upper_control_limit=float(mean + 3 * std),
                    lower_control_limit=float(mean - 3 * std),
                    description="9 consecutive points above the mean",
                ))
            elif below_count >= 9:
                violations.append(SPCViolation(
                    rule_name="Rule 2 — 9 points on same side of center (below)",
                    machine_id=machine_id,
                    parameter_name=parameter_name,
                    severity="warning",
                    value=last_value,
                    upper_control_limit=float(mean + 3 * std),
                    lower_control_limit=float(mean - 3 * std),
                    description="9 consecutive points below the mean",
                ))

        # Rule 3: 6 points trending (monotonic)
        if len(values) >= 6:
            last_6 = values[-6:]
            increasing = all(last_6[i] < last_6[i + 1] for i in range(5))
            decreasing = all(last_6[i] > last_6[i + 1] for i in range(5))
            if increasing:
                violations.append(SPCViolation(
                    rule_name="Rule 3 — 6 points trending up",
                    machine_id=machine_id,
                    parameter_name=parameter_name,
                    severity="alert",
                    value=last_value,
                    upper_control_limit=float(mean + 3 * std),
                    lower_control_limit=float(mean - 3 * std),
                    description="6 consecutive increasing values",
                ))
            elif decreasing:
                violations.append(SPCViolation(
                    rule_name="Rule 3 — 6 points trending down",
                    machine_id=machine_id,
                    parameter_name=parameter_name,
                    severity="alert",
                    value=last_value,
                    upper_control_limit=float(mean + 3 * std),
                    lower_control_limit=float(mean - 3 * std),
                    description="6 consecutive decreasing values",
                ))

        # Rule 4: 14 points alternating up/down
        if len(values) >= 14:
            last_14 = values[-14:]
            alternating = all(
                (last_14[i] - last_14[i + 1]) * (last_14[i + 1] - last_14[i + 2]) < 0
                for i in range(12)
            )
            if alternating:
                violations.append(SPCViolation(
                    rule_name="Rule 4 — 14 points alternating",
                    machine_id=machine_id,
                    parameter_name=parameter_name,
                    severity="info",
                    value=last_value,
                    upper_control_limit=float(mean + 3 * std),
                    lower_control_limit=float(mean - 3 * std),
                    description="14 consecutive alternating values (potential over-control)",
                ))

        # Rule 5: 2 of 3 points beyond ±2σ (Zone A)
        if len(values) >= 3:
            last_3 = values[-3:]
            beyond_2sigma = sum(1 for v in last_3 if abs(v - mean) > 2 * std)
            if beyond_2sigma >= 2:
                violations.append(SPCViolation(
                    rule_name="Rule 5 — 2 of 3 points beyond ±2σ",
                    machine_id=machine_id,
                    parameter_name=parameter_name,
                    severity="alert",
                    value=last_value,
                    upper_control_limit=float(mean + 3 * std),
                    lower_control_limit=float(mean - 3 * std),
                    description="2 out of 3 consecutive points beyond ±2σ",
                ))

        # Rule 6: 4 of 5 points beyond ±1σ (Zone B)
        if len(values) >= 5:
            last_5 = values[-5:]
            beyond_1sigma = sum(1 for v in last_5 if abs(v - mean) > 1 * std)
            if beyond_1sigma >= 4:
                violations.append(SPCViolation(
                    rule_name="Rule 6 — 4 of 5 points beyond ±1σ",
                    machine_id=machine_id,
                    parameter_name=parameter_name,
                    severity="alert",
                    value=last_value,
                    upper_control_limit=float(mean + 3 * std),
                    lower_control_limit=float(mean - 3 * std),
                    description="4 out of 5 consecutive points beyond ±1σ",
                ))

        return violations

    def identify_bottleneck(
        self,
        machine_stats: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Identify the bottleneck machine from utilization statistics.

        Args:
            machine_stats: List of dicts with keys:
                machine_id, utilization_pct, cycle_time_seconds, queue_length

        Returns:
            dict with bottleneck analysis
        """
        if not machine_stats:
            return {
                "bottleneck_machine_id": "",
                "constraint_type": "no_data",
                "recommendations": ["No machine data available for analysis"],
            }

        # Bottleneck = highest utilization machine (Theory of Constraints)
        bottleneck = max(machine_stats, key=lambda m: m.get("utilization_pct", 0))
        utilization = bottleneck.get("utilization_pct", 0)
        cycle_time = bottleneck.get("cycle_time_seconds", 0)

        # Determine constraint type
        if utilization >= 95:
            constraint_type = "capacity"
        elif utilization >= 85:
            constraint_type = "near_capacity"
        else:
            constraint_type = "other"

        # Generate recommendations
        recommendations = [
            f"Increase throughput on {bottleneck.get('machine_id', 'unknown')} "
            f"(utilization: {utilization:.1f}%)"
        ]

        if cycle_time > 0:
            recommendations.append(
                f"Consider reducing cycle time from {cycle_time:.1f}s "
                f"or adding parallel operation"
            )

        queue_length = bottleneck.get("queue_length", 0)
        if queue_length > 10:
            recommendations.append(
                f"Queue length is {queue_length} — consider upstream throttling"
            )

        return {
            "bottleneck_machine_id": bottleneck.get("machine_id", ""),
            "constraint_type": constraint_type,
            "utilization_pct": utilization,
            "cycle_time_seconds": cycle_time,
            "queue_length": queue_length,
            "recommendations": recommendations,
        }

    def compute_yield_optimization(
        self,
        current_yield_pct: float,
        target_yield_pct: float,
        parameter_history: dict[str, list[float]],
        defect_correlation: dict[str, float],
    ) -> dict[str, Any]:
        """Compute yield optimization recommendations.

        Args:
            current_yield_pct: Current yield percentage
            target_yield_pct: Target yield percentage
            parameter_history: Dict of parameter_name -> [values]
            defect_correlation: Dict of parameter_name -> correlation with defects

        Returns:
            dict with parameter adjustments and expected improvement
        """
        if not parameter_history:
            return {
                "current_yield_pct": current_yield_pct,
                "target_yield_pct": target_yield_pct,
                "parameter_adjustments": {},
                "expected_improvement_pct": 0.0,
                "recommendations": ["No parameter history available for analysis"],
            }

        # Sort parameters by absolute correlation with defects (descending)
        sorted_params = sorted(
            defect_correlation.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        )

        parameter_adjustments: dict[str, float] = {}
        total_improvement = 0.0
        recommendations = []

        for param_name, correlation in sorted_params[:5]:  # top 5 correlated params
            history = parameter_history.get(param_name, [])
            if len(history) < 10:
                continue

            # Compute optimal parameter value based on history
            mean_val = float(np.mean(history))
            std_val = float(np.std(history))

            if abs(correlation) > 0.3 and std_val > 0:
                # Suggest adjustment toward better value
                adjustment = -correlation * 0.5 * std_val  # move opposite to defect direction
                parameter_adjustments[param_name] = round(adjustment, 2)
                expected_gain = min(abs(correlation) * 2.0, 5.0)  # max 5% per param
                total_improvement += expected_gain
                recommendations.append(
                    f"Adjust {param_name} by {adjustment:+.2f} "
                    f"(correlation: {correlation:+.2f}, expected gain: {expected_gain:+.1f}%)"
                )

        expected_improvement = min(total_improvement, target_yield_pct - current_yield_pct)
        expected_improvement = max(expected_improvement, 0.0)

        return {
            "current_yield_pct": current_yield_pct,
            "target_yield_pct": target_yield_pct,
            "parameter_adjustments": parameter_adjustments,
            "expected_improvement_pct": round(expected_improvement, 2),
            "recommendations": recommendations,
        }

    # ──────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────

    def _update_history(self, production_line: str, oee_pct: float) -> None:
        """Add OEE value to rolling history for trend analysis."""
        if production_line not in self._history:
            self._history[production_line] = []
        self._history[production_line].append(oee_pct)
        # Keep only the last N values
        if len(self._history[production_line]) > self.history_window:
            self._history[production_line] = self._history[production_line][-self.history_window:]

    def _compute_trend(self, production_line: str) -> TrendDirection:
        """Compute trend direction based on linear regression slope."""
        history = self._history.get(production_line, [])
        if len(history) < 3:
            return TrendDirection.STABLE

        x = np.arange(len(history))
        y = np.array(history)

        try:
            slope = np.polyfit(x, y, 1)[0]
        except np.linalg.LinAlgError:
            return TrendDirection.STABLE

        if slope > 0.5:
            return TrendDirection.IMPROVING
        elif slope < -0.5:
            return TrendDirection.DECLINING
        return TrendDirection.STABLE
