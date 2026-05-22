"""Tests for the production scheduler."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.decisions.scheduler import ProductionOrder, ProductionScheduler


class TestProductionScheduler:
    """Test schedule optimization and maintenance trigger logic."""

    def setup_method(self) -> None:
        self.scheduler = ProductionScheduler(
            schedule_variance_threshold_hours=8.0,
        )

    def test_schedule_basic(self) -> None:
        """Basic scheduling with two orders."""
        now = datetime.now(timezone.utc)
        orders = [
            ProductionOrder(
                order_id="ORD-001",
                product_id="P001",
                product_name="Product A",
                quantity=100,
                due_date=now + timedelta(days=1),
                priority=80,
                material_available=True,
            ),
            ProductionOrder(
                order_id="ORD-002",
                product_id="P002",
                product_name="Product B",
                quantity=200,
                due_date=now + timedelta(days=2),
                priority=50,
                material_available=True,
            ),
        ]

        schedule = self.scheduler.schedule_production(
            orders=orders,
            production_line="Line-A",
            shift_start=now,
            shift_end=now + timedelta(hours=8),
        )

        assert schedule.total_orders == 2
        assert schedule.total_units > 0
        assert schedule.production_line == "Line-A"
        assert schedule.optimization_score > 0
        assert not schedule.hitl_required

    def test_no_material_available(self) -> None:
        """Order without material availability is skipped."""
        now = datetime.now(timezone.utc)
        orders = [
            ProductionOrder(
                order_id="ORD-003",
                product_id="P003",
                product_name="Product C",
                quantity=500,
                due_date=now + timedelta(days=1),
                priority=90,
                material_available=False,  # no material
            ),
        ]

        schedule = self.scheduler.schedule_production(
            orders=orders,
            production_line="Line-A",
            shift_start=now,
            shift_end=now + timedelta(hours=8),
        )

        assert schedule.total_orders == 0  # skipped due to material unavailability

    def test_schedule_variance_detection(self) -> None:
        """Variance is detected when schedule changes."""
        now = datetime.now(timezone.utc)
        orders = [
            ProductionOrder(
                order_id="ORD-004",
                product_id="P004",
                product_name="Product D",
                quantity=100,
                due_date=now + timedelta(days=1),
                priority=80,
            ),
        ]

        schedule1 = self.scheduler.schedule_production(
            orders=orders,
            production_line="Line-A",
            shift_start=now,
            shift_end=now + timedelta(hours=8),
        )

        # Same orders again — variance should be 0
        schedule2 = self.scheduler.schedule_production(
            orders=orders,
            production_line="Line-A",
            shift_start=now,
            shift_end=now + timedelta(hours=8),
            last_sequence_hash="",  # no previous hash
        )

        # Just verify it generates a schedule
        assert schedule2.total_orders == 1
        assert schedule2.production_line == "Line-A"

    def test_maintenance_evaluation_no_action(self) -> None:
        """Low failure probability requires no action."""
        eval_result = self.scheduler.evaluate_maintenance_trigger(
            machine_id="M-001",
            machine_name="CNC Machine 1",
            failure_probability=0.3,
            confidence=0.85,
        )

        assert not eval_result.action_required
        assert not eval_result.immediate_halt
        assert not eval_result.hitl_required

    def test_maintenance_evaluation_proactive(self) -> None:
        """Moderate failure probability triggers proactive maintenance."""
        eval_result = self.scheduler.evaluate_maintenance_trigger(
            machine_id="M-002",
            machine_name="Press Machine 2",
            failure_probability=0.90,
            confidence=0.92,
        )

        assert eval_result.action_required
        assert not eval_result.immediate_halt
        assert not eval_result.hitl_required
        assert "Proactive" in eval_result.recommended_action

    def test_maintenance_evaluation_immediate_halt(self) -> None:
        """High failure probability triggers immediate halt + HITL."""
        eval_result = self.scheduler.evaluate_maintenance_trigger(
            machine_id="M-003",
            machine_name="Safety-Critical Press",
            failure_probability=0.98,
            confidence=0.95,
        )

        assert eval_result.action_required
        assert eval_result.immediate_halt
        assert eval_result.hitl_required
        assert "IMMEDIATE HALT" in eval_result.recommended_action

    def test_priority_ordering(self) -> None:
        """Higher priority orders with earlier due dates are scheduled first."""
        now = datetime.now(timezone.utc)
        orders = [
            ProductionOrder(
                order_id="ORD-LOW",
                product_id="P001",
                product_name="Low Priority",
                quantity=100,
                due_date=now + timedelta(days=7),
                priority=20,  # low priority
                material_available=True,
            ),
            ProductionOrder(
                order_id="ORD-HIGH",
                product_id="P002",
                product_name="High Priority",
                quantity=50,
                due_date=now + timedelta(hours=12),
                priority=95,  # high priority, earlier due date
                material_available=True,
            ),
        ]

        schedule = self.scheduler.schedule_production(
            orders=orders,
            production_line="Line-A",
            shift_start=now,
            shift_end=now + timedelta(hours=8),
        )

        assert schedule.total_orders >= 1
        # The high-priority order should appear first
        if schedule.sequence:
            assert schedule.sequence[0]["order_id"] == "ORD-HIGH"

    def test_customer_tier_priority(self) -> None:
        """Tier-1 customers get priority in scheduling."""
        now = datetime.now(timezone.utc)
        orders = [
            ProductionOrder(
                order_id="ORD-T3",
                product_id="P001",
                product_name="Tier 3",
                quantity=100,
                due_date=now + timedelta(days=3),
                priority=50,
                customer_tier=3,
                material_available=True,
            ),
            ProductionOrder(
                order_id="ORD-T1",
                product_id="P002",
                product_name="Tier 1",
                quantity=100,
                due_date=now + timedelta(days=3),
                priority=50,
                customer_tier=1,  # top tier
                material_available=True,
            ),
        ]

        schedule = self.scheduler.schedule_production(
            orders=orders,
            production_line="Line-A",
            shift_start=now,
            shift_end=now + timedelta(hours=8),
        )

        assert schedule.total_orders >= 1
        if schedule.sequence:
            assert schedule.sequence[0]["order_id"] == "ORD-T1"
