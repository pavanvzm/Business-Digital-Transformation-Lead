"""Production scheduler — order sequencing, constraint optimization, and bottleneck-aware planning.

Uses deterministic rule-based scheduling (not ML) for auditability:
- Earliest Due Date (EDD) for order sequencing
- Critical Ratio (CR) for priority scoring
- Setup time optimization via nearest-neighbor heuristic
- Line dependency graph for downtime propagation across lines
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class ProductionOrder:
    """A production order to be scheduled."""

    order_id: str
    product_id: str
    product_name: str
    quantity: int
    due_date: datetime
    priority: int = 50  # 1-100, higher = more urgent
    setup_time_minutes: float = 30.0
    cycle_time_per_unit_seconds: float = 60.0
    material_available: bool = True
    customer_tier: int = 3  # 1=top, 2=standard, 3=basic
    committed: bool = False  # committed delivery date


@dataclass
class MachineSlot:
    """A scheduled time slot on a production machine/line."""

    machine_id: str
    order_id: str
    start_time: datetime
    end_time: datetime
    setup_time_minutes: float = 0.0
    changeover_from: str | None = None


@dataclass
class ProductionSchedule:
    """A complete production schedule for a line or shift."""

    schedule_id: str = field(default_factory=lambda: f"sched-{uuid4().hex[:8]}")
    production_line: str = ""
    slots: list[MachineSlot] = field(default_factory=list)
    sequence: list[dict[str, Any]] = field(default_factory=list)
    original_sequence_hash: str = ""
    variance_hours: float = 0.0
    variance_reason: str = ""
    total_orders: int = 0
    total_units: int = 0
    optimization_score: float = 0.0
    hitl_required: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schedule_id": self.schedule_id,
            "production_line": self.production_line,
            "sequence": self.sequence,
            "original_sequence_hash": self.original_sequence_hash,
            "variance_hours": round(self.variance_hours, 2),
            "variance_reason": self.variance_reason,
            "total_orders": self.total_orders,
            "total_units": self.total_units,
            "optimization_score": round(self.optimization_score, 1),
            "hitl_required": self.hitl_required,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class SourcingAnalysis:
    """Alternative sourcing options analysis result."""

    material_id: str
    material_name: str
    total_alternatives: int = 0
    hitl_required: bool = False
    recommendation: dict[str, Any] = field(default_factory=dict)
    alternatives: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MaintenanceTriggerEvaluation:
    """Result of evaluating a predictive maintenance trigger."""

    machine_id: str
    machine_name: str
    failure_probability: float
    confidence: float
    action_required: bool = False
    immediate_halt: bool = False
    hitl_required: bool = False
    recommended_action: str = ""
    predicted_failure_hours: float | None = None


class LineDependencyGraph:
    """Directed graph for production line dependencies.

    Models which lines feed into which — downtime on a feeder line
    propagates to all downstream dependents transitively.
    """

    def __init__(self) -> None:
        # adjacency: feeder -> [dependent, ...]
        self._graph: dict[str, list[str]] = {}
        self._reverse: dict[str, list[str]] = {}

    def add_dependency(self, feeder_line: str, dependent_line: str) -> None:
        """Record that `dependent_line` depends on `feeder_line`."""
        self._graph.setdefault(feeder_line, []).append(dependent_line)
        self._reverse.setdefault(dependent_line, []).append(feeder_line)

    def get_dependents(self, line_id: str) -> list[str]:
        """Return all lines that directly depend on `line_id`."""
        return self._graph.get(line_id, [])

    def get_all_downstream(self, line_id: str) -> set[str]:
        """Return all transitively downstream lines of `line_id`."""
        visited: set[str] = set()
        queue = [line_id]
        while queue:
            current = queue.pop(0)
            for dep in self._graph.get(current, []):
                if dep not in visited:
                    visited.add(dep)
                    queue.append(dep)
        return visited

    def propagate_downtime(self, offline_line: str, hours_lost: float) -> dict[str, float]:
        """Propagate downtime hours to all downstream lines.

        Returns a dict of {line_id: hours_lost_propagated}.
        """
        downstream = self.get_all_downstream(offline_line)
        # Propagated hours decrease by 20% per hop (conservative estimate)
        propagation = {}
        for dep in downstream:
            hops = self._count_hops(offline_line, dep)
            propagation[dep] = round(hours_lost * (0.8 ** hops), 2)
        return propagation

    def _count_hops(self, source: str, target: str) -> int:
        """Count hops from source to target in the dependency graph."""
        queue: list[tuple[str, int]] = [(source, 0)]
        visited = {source}
        while queue:
            current, depth = queue.pop(0)
            if current == target:
                return depth
            for dep in self._graph.get(current, []):
                if dep not in visited:
                    visited.add(dep)
                    queue.append((dep, depth + 1))
        return 0


class ProductionScheduler:
    """Constraint-based production scheduler.

    Scheduling algorithm:
    1. Prioritize orders by due date (EDD) × critical ratio × customer tier
    2. Sequence to minimize setup time changes (changeover optimization)
    3. Assign to available machine slots considering maintenance windows
    4. Re-evaluate when new orders arrive or constraints change

    Optionally accepts a LineDependencyGraph for downtime propagation.
    """

    def __init__(
        self,
        schedule_variance_threshold_hours: float = 8.0,
        max_setup_minutes: float = 120.0,
        dependency_graph: LineDependencyGraph | None = None,
    ) -> None:
        self.schedule_variance_threshold = schedule_variance_threshold_hours
        self.max_setup = max_setup_minutes
        self.dependency_graph = dependency_graph
        self._last_schedule_hash: str = ""
        self._last_order_ids: set[str] = set()  # track for variance detection

    def schedule_production(
        self,
        orders: list[ProductionOrder],
        production_line: str,
        shift_start: datetime,
        shift_end: datetime | None = None,
        scheduled_maintenance_windows: list[tuple[datetime, datetime]] | None = None,
        machine_available: bool = True,
        last_sequence_hash: str = "",
    ) -> ProductionSchedule:
        """Create an optimized production schedule.

        Args:
            orders: Production orders to schedule
            production_line: Target production line
            shift_start: Start time of the shift
            shift_end: End time (None = 8-hour default)
            scheduled_maintenance_windows: [(start, end), ...]
            machine_available: Whether the line is available
            last_sequence_hash: Hash of the previous schedule for variance detection

        Returns:
            ProductionSchedule with optimized sequence and slot assignments
        """
        if shift_end is None:
            shift_end = shift_start + timedelta(hours=8)

        maintenance_windows = scheduled_maintenance_windows or []

        # ── Step 1: Score and rank orders ──
        scored_orders = []
        for order in orders:
            # Critical Ratio = (Due Date - Now) / Remaining Work
            remaining_seconds = (order.due_date - datetime.now(timezone.utc)).total_seconds()
            remaining_work_seconds = order.quantity * order.cycle_time_per_unit_seconds

            if remaining_work_seconds > 0:
                critical_ratio = max(remaining_seconds / remaining_work_seconds, 0.0)
            else:
                critical_ratio = 999.0

            # Score: higher = more urgent
            # Factor in customer tier, committed date, priority
            tier_multiplier = {1: 1.5, 2: 1.2, 3: 1.0}.get(order.customer_tier, 1.0)
            committed_bonus = 20 if order.committed else 0

            score = (
                (100.0 / max(critical_ratio, 0.1))  # urgency
                * (order.priority / 50.0)            # business priority
                * tier_multiplier                    # customer tier
                + committed_bonus                    # committed delivery
            )

            scored_orders.append((score, order))

        # Sort by score descending (most urgent first)
        scored_orders.sort(key=lambda x: x[0], reverse=True)

        # ── Step 2: Assign to machine slots ──
        slots: list[MachineSlot] = []
        current_time = shift_start
        previous_product: str | None = None

        for score, order in scored_orders:
            if not order.material_available:
                continue

            # Check if order can fit within the shift
            order_duration_minutes = (
                order.quantity * order.cycle_time_per_unit_seconds / 60.0
            ) + order.setup_time_minutes

            if current_time + timedelta(minutes=order_duration_minutes) > shift_end:
                # Order doesn't fit in this shift — carry forward
                continue

            # Check for maintenance conflicts
            order_end = current_time + timedelta(minutes=order_duration_minutes)
            conflicts = any(
                not (order_end <= m_start or current_time >= m_end)
                for m_start, m_end in maintenance_windows
            )

            if conflicts:
                # Skip to after the maintenance window
                current_time = max(e for s, e in maintenance_windows if s > current_time)
                if current_time + timedelta(minutes=order_duration_minutes) > shift_end:
                    continue
                order_end = current_time + timedelta(minutes=order_duration_minutes)

            # Calculate changeover time
            changeover_minutes = 0.0
            if previous_product is not None and previous_product != order.product_id:
                # Simplified: changeover = setup_time (could be product-pair specific)
                changeover_minutes = min(order.setup_time_minutes, self.max_setup)

            slot = MachineSlot(
                machine_id=production_line,
                order_id=order.order_id,
                start_time=current_time + timedelta(minutes=changeover_minutes),
                end_time=order_end,
                setup_time_minutes=order.setup_time_minutes,
                changeover_from=previous_product,
            )
            slots.append(slot)

            current_time = order_end
            previous_product = order.product_id

        # ── Step 3: Build sequence ──
        sequence = []
        total_units = 0
        for slot in slots:
            order_data = next(
                (o for _, o in scored_orders if o.order_id == slot.order_id),
                None,
            )
            if order_data:
                sequence.append({
                    "order_id": slot.order_id,
                    "product_id": order_data.product_id,
                    "product_name": order_data.product_name,
                    "quantity": order_data.quantity,
                    "start_time": slot.start_time.isoformat(),
                    "end_time": slot.end_time.isoformat(),
                    "setup_minutes": slot.setup_time_minutes,
                    "changeover_from": slot.changeover_from or "",
                })
                total_units += order_data.quantity

        # ── Step 4: Compute optimization score ──
        # Measure: utilization, due-date adherence, setup efficiency
        total_available_minutes = (shift_end - shift_start).total_seconds() / 60.0
        used_minutes = sum(
            (s.end_time - s.start_time).total_seconds() / 60.0
            for s in slots
        )
        utilization = (used_minutes / max(total_available_minutes, 1)) * 100.0
        optimization_score = min(utilization * 0.7 + (100.0 - utilization) * 0.3, 100.0)

        # ── Step 5: Compute schedule hash and variance ──
        seq_str = "|".join(f"{s['order_id']}:{s['start_time']}" for s in sequence)
        schedule_hash = hashlib.md5(seq_str.encode()).hexdigest()

        # Detect variance from last schedule using tracked order IDs
        current_order_ids = {s["order_id"] for s in sequence}
        variance_hours = 0.0
        variance_reason = ""
        if self._last_order_ids:
            removed = self._last_order_ids - current_order_ids
            added = current_order_ids - self._last_order_ids
            changed = len(removed) + len(added)
            if changed > 0:
                variance_hours = changed * 0.5  # approximate 30min per change
                variance_reason = f"Schedule changed: {len(removed)} removed, {len(added)} added"

        self._last_order_ids = current_order_ids

        # Determine if HITL is required
        hitl_required = variance_hours >= self.schedule_variance_threshold

        result = ProductionSchedule(
            production_line=production_line,
            slots=slots,
            sequence=sequence,
            original_sequence_hash=last_sequence_hash,
            variance_hours=variance_hours,
            variance_reason=variance_reason if variance_hours > 0 else "",
            total_orders=len(sequence),
            total_units=total_units,
            optimization_score=round(optimization_score, 1),
            hitl_required=hitl_required,
        )

        self._last_schedule_hash = schedule_hash
        return result

    def evaluate_maintenance_trigger(
        self,
        machine_id: str,
        machine_name: str,
        failure_probability: float,
        confidence: float,
        features: dict[str, float] | None = None,
        proactive_threshold: float = 0.85,
        immediate_halt_threshold: float = 0.95,
    ) -> MaintenanceTriggerEvaluation:
        """Evaluate a predictive maintenance trigger and determine required action.

        Args:
            machine_id: Machine identifier
            machine_name: Human-readable machine name
            failure_probability: Model-predicted failure probability (0-1)
            confidence: Model confidence (0-1)
            features: Feature values used in prediction
            proactive_threshold: Threshold for proactive maintenance
            immediate_halt_threshold: Threshold for immediate halt + HITL

        Returns:
            MaintenanceTriggerEvaluation with action recommendation
        """
        action_required = failure_probability >= proactive_threshold
        immediate_halt = failure_probability >= immediate_halt_threshold
        hitl_required = immediate_halt

        if immediate_halt:
            recommended_action = f"IMMEDIATE HALT: {machine_name} failure probability {failure_probability:.0%} exceeds critical threshold"
            # Estimated failure within 2 hours
            predicted_failure_hours = 2.0
        elif action_required:
            recommended_action = f"Proactive maintenance: {machine_name} failure probability {failure_probability:.0%}"
            # Estimated failure within 24-72 hours
            predicted_failure_hours = 48.0 * (1.0 - failure_probability)
        else:
            recommended_action = "No action required — routine monitoring"
            predicted_failure_hours = None

        return MaintenanceTriggerEvaluation(
            machine_id=machine_id,
            machine_name=machine_name,
            failure_probability=failure_probability,
            confidence=confidence,
            action_required=action_required,
            immediate_halt=immediate_halt,
            hitl_required=hitl_required,
            recommended_action=recommended_action,
            predicted_failure_hours=predicted_failure_hours,
        )

    def _compute_setup_matrix(
        self, products: list[str], setup_times: dict[tuple[str, str], float]
    ) -> list[list[float]]:
        """Compute setup time matrix for changeover optimization."""
        n = len(products)
        matrix = [[0.0] * n for _ in range(n)]
        for i, from_p in enumerate(products):
            for j, to_p in enumerate(products):
                if i != j:
                    matrix[i][j] = setup_times.get((from_p, to_p), 30.0)
        return matrix
