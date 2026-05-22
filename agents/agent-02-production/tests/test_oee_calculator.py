"""Tests for the OEE calculator engine and SPC rule checking."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.scoring.oee_calculator import OEECalculator, TrendDirection


class TestOEECalculator:
    """Test OEE calculation with various scenarios."""

    def setup_method(self) -> None:
        self.calculator = OEECalculator()

    def test_perfect_oee(self) -> None:
        """100% OEE when everything is perfect."""
        result = self.calculator.calculate_oee(
            production_line="Line-A",
            shift_id="S1",
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            operating_time_minutes=480.0,
            planned_production_time_minutes=480.0,
            ideal_cycle_time_seconds=60.0,
            total_units_produced=480,
            total_good_units=480,
            total_defective_units=0,
            total_downtime_minutes=0.0,
            planned_downtime_minutes=0.0,
        )

        assert result.availability_pct == 100.0
        assert result.performance_pct == 100.0
        assert result.quality_pct == 100.0
        assert result.oee_pct == 100.0
        assert result.trend == TrendDirection.STABLE

    def test_low_availability(self) -> None:
        """OEE when machine is down 2 hours of an 8-hour shift."""
        result = self.calculator.calculate_oee(
            production_line="Line-A",
            shift_id="S2",
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            operating_time_minutes=360.0,  # 6 hours operating
            planned_production_time_minutes=480.0,  # 8 hours planned
            ideal_cycle_time_seconds=60.0,
            total_units_produced=360,
            total_good_units=350,
            total_defective_units=10,
            total_downtime_minutes=120.0,
            planned_downtime_minutes=30.0,
        )

        assert result.availability_pct == 75.0  # 360/480
        assert result.quality_pct > 95.0
        assert result.oee_pct < 80.0

    def test_quality_issues(self) -> None:
        """OEE with high defect rate."""
        result = self.calculator.calculate_oee(
            production_line="Line-B",
            shift_id="S1",
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            operating_time_minutes=450.0,
            planned_production_time_minutes=480.0,
            ideal_cycle_time_seconds=60.0,
            total_units_produced=450,
            total_good_units=400,
            total_defective_units=50,
            total_downtime_minutes=30.0,
            planned_downtime_minutes=15.0,
        )

        assert result.quality_pct == pytest.approx(88.89, rel=0.01)  # 400/450
        assert result.oee_pct > 0
        assert result.availability_pct == 93.75  # 450/480

    def test_trend_detection(self) -> None:
        """Trend detection from multiple OEE values."""
        calc = OEECalculator(history_window=5)

        # Simulate declining OEE over multiple periods
        for i in range(6):
            calc.calculate_oee(
                production_line="Line-C",
                shift_id="S1",
                period_start=datetime.now(timezone.utc),
                period_end=datetime.now(timezone.utc),
                operating_time_minutes=480.0 - (i * 30),
                planned_production_time_minutes=480.0,
                ideal_cycle_time_seconds=60.0,
                total_units_produced=480 - (i * 20),
                total_good_units=470 - (i * 25),
                total_defective_units=10 + (i * 5),
                total_downtime_minutes=float(i * 10),
                planned_downtime_minutes=0.0,
            )

        result = calc.calculate_oee(
            production_line="Line-C",
            shift_id="S1",
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            operating_time_minutes=300.0,
            planned_production_time_minutes=480.0,
            ideal_cycle_time_seconds=60.0,
            total_units_produced=300,
            total_good_units=280,
            total_defective_units=20,
            total_downtime_minutes=60.0,
            planned_downtime_minutes=0.0,
        )

        assert result.trend == TrendDirection.DECLINING

    def test_zero_production(self) -> None:
        """OEE when no units produced."""
        result = self.calculator.calculate_oee(
            production_line="Line-D",
            shift_id="S1",
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            operating_time_minutes=0.0,
            planned_production_time_minutes=480.0,
            ideal_cycle_time_seconds=60.0,
            total_units_produced=0,
            total_good_units=0,
            total_defective_units=0,
            total_downtime_minutes=480.0,
            planned_downtime_minutes=0.0,
        )

        assert result.availability_pct == 0.0
        assert result.performance_pct == 0.0
        assert result.oee_pct == 0.0

    def test_invalid_negative_durations(self) -> None:
        """OEE with negative durations marks result as invalid."""
        result = self.calculator.calculate_oee(
            production_line="Line-E",
            shift_id="S1",
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            operating_time_minutes=-10.0,  # negative — invalid
            planned_production_time_minutes=480.0,
            ideal_cycle_time_seconds=60.0,
            total_units_produced=100,
            total_good_units=95,
            total_defective_units=5,
            total_downtime_minutes=10.0,
            planned_downtime_minutes=5.0,
        )

        assert not result.is_valid
        assert result.oee_pct > 0  # still computed, but flagged invalid

    def test_invalid_zero_cycle_time(self) -> None:
        """OEE with zero cycle time marks result as invalid."""
        result = self.calculator.calculate_oee(
            production_line="Line-F",
            shift_id="S1",
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            operating_time_minutes=480.0,
            planned_production_time_minutes=480.0,
            ideal_cycle_time_seconds=0.0,  # zero cycle time
            total_units_produced=100,
            total_good_units=95,
            total_defective_units=5,
            total_downtime_minutes=0.0,
            planned_downtime_minutes=0.0,
        )

        assert not result.is_valid

    def test_invalid_defect_mismatch(self) -> None:
        """OEE with more defects than total units marks result as invalid."""
        result = self.calculator.calculate_oee(
            production_line="Line-G",
            shift_id="S1",
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            operating_time_minutes=480.0,
            planned_production_time_minutes=480.0,
            ideal_cycle_time_seconds=60.0,
            total_units_produced=100,
            total_good_units=50,
            total_defective_units=60,  # more defective than total — invalid
            total_downtime_minutes=0.0,
            planned_downtime_minutes=0.0,
        )

        assert not result.is_valid

    def test_loss_breakdown_present(self) -> None:
        """OEE breakdown includes 6-loss decomposition when data is valid."""
        result = self.calculator.calculate_oee(
            production_line="Line-H",
            shift_id="S1",
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            operating_time_minutes=360.0,
            planned_production_time_minutes=480.0,
            ideal_cycle_time_seconds=60.0,
            total_units_produced=360,
            total_good_units=340,
            total_defective_units=20,
            total_downtime_minutes=120.0,
            planned_downtime_minutes=30.0,
        )

        lb = result.loss_breakdown
        assert "equipment_failure_loss_pct" in lb
        assert "setup_adjustment_loss_pct" in lb
        assert "idling_minor_stops_loss_pct" in lb
        assert "reduced_speed_loss_pct" in lb
        assert "defect_process_loss_pct" in lb
        assert "reduced_yield_loss_pct" in lb
        assert len(lb) == 6

    def test_to_dict_serialization(self) -> None:
        """OEE breakdown serialization to dict includes new fields."""
        result = self.calculator.calculate_oee(
            production_line="Line-A",
            shift_id="S1",
            period_start=datetime(2026, 1, 15, tzinfo=timezone.utc),
            period_end=datetime(2026, 1, 15, tzinfo=timezone.utc),
            operating_time_minutes=450.0,
            planned_production_time_minutes=480.0,
            ideal_cycle_time_seconds=60.0,
            total_units_produced=450,
            total_good_units=440,
            total_defective_units=10,
            total_downtime_minutes=30.0,
            planned_downtime_minutes=15.0,
        )

        d = result.to_dict()
        assert d["production_line"] == "Line-A"
        assert d["shift_id"] == "S1"
        assert d["oee_pct"] > 0
        assert d["is_valid"] is True
        assert "loss_breakdown" in d
        assert len(d["components"]) == 3
        assert all(c["name"] in ("availability", "performance", "quality") for c in d["components"])


class TestSPCRules:
    """Test Statistical Process Control rule checking."""

    def setup_method(self) -> None:
        self.calculator = OEECalculator()

    def test_rule1_beyond_3sigma(self) -> None:
        """Rule 1: Single point beyond ±3σ."""
        values = [50.0] * 20 + [200.0]  # last point far beyond
        violations = self.calculator.check_spc_rules(
            machine_id="M-001",
            parameter_name="temperature",
            values=values,
            mean=50.0,
            std=10.0,
        )
        rule1_violations = [v for v in violations if "Rule 1" in v.rule_name]
        assert len(rule1_violations) == 1

    def test_rule2_nine_above(self) -> None:
        """Rule 2: 9 points on same side of center."""
        values = [60.0] * 9  # all above mean of 50
        violations = self.calculator.check_spc_rules(
            machine_id="M-002",
            parameter_name="pressure",
            values=values,
            mean=50.0,
            std=5.0,
        )
        rule2_violations = [v for v in violations if "Rule 2" in v.rule_name]
        assert len(rule2_violations) == 1

    def test_rule3_six_trending(self) -> None:
        """Rule 3: 6 points trending up."""
        values = [50, 52, 54, 56, 58, 60]
        violations = self.calculator.check_spc_rules(
            machine_id="M-003",
            parameter_name="temperature",
            values=values,
            mean=50.0,
            std=5.0,
        )
        rule3_violations = [v for v in violations if "Rule 3" in v.rule_name]
        assert len(rule3_violations) == 1

    def test_rule4_alternating(self) -> None:
        """Rule 4: 14 points alternating."""
        values = [50, 55, 50, 55, 50, 55, 50, 55, 50, 55, 50, 55, 50, 55]
        violations = self.calculator.check_spc_rules(
            machine_id="M-004",
            parameter_name="flow_rate",
            values=values,
            mean=52.5,
            std=2.5,
        )
        rule4_violations = [v for v in violations if "Rule 4" in v.rule_name]
        assert len(rule4_violations) == 1

    def test_rule5_2_of_3_beyond_2sigma(self) -> None:
        """Rule 5: 2 of 3 points beyond ±2σ."""
        values = [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 30, 50, 30]
        violations = self.calculator.check_spc_rules(
            machine_id="M-005",
            parameter_name="vibration",
            values=values,
            mean=50.0,
            std=5.0,
        )
        rule5_violations = [v for v in violations if "Rule 5" in v.rule_name]
        assert len(rule5_violations) == 1

    def test_rule6_4_of_5_beyond_1sigma(self) -> None:
        """Rule 6: 4 of 5 points beyond ±1σ."""
        values = [50, 50, 50, 50, 50, 43, 43, 43, 43, 60]
        violations = self.calculator.check_spc_rules(
            machine_id="M-006",
            parameter_name="current_draw",
            values=values,
            mean=50.0,
            std=5.0,
        )
        rule6_violations = [v for v in violations if "Rule 6" in v.rule_name]
        assert len(rule6_violations) >= 1

    def test_no_violations(self) -> None:
        """No violations when data is in control."""
        values = [50.0] * 20
        violations = self.calculator.check_spc_rules(
            machine_id="M-007",
            parameter_name="temperature",
            values=values,
            mean=50.0,
            std=5.0,
        )
        assert len(violations) == 0

    def test_insufficient_data(self) -> None:
        """No rules triggered with too few data points."""
        values = [50.0, 55.0]
        violations = self.calculator.check_spc_rules(
            machine_id="M-008",
            parameter_name="temperature",
            values=values,
        )
        assert len(violations) == 0


class TestBottleneckAnalysis:
    """Test bottleneck identification logic."""

    def setup_method(self) -> None:
        self.calculator = OEECalculator()

    def test_high_utilization_bottleneck(self) -> None:
        """Bottleneck identified as highest utilization machine."""
        machines = [
            {"machine_id": "M-001", "utilization_pct": 95.0, "cycle_time_seconds": 60.0, "queue_length": 15},
            {"machine_id": "M-002", "utilization_pct": 65.0, "cycle_time_seconds": 45.0, "queue_length": 3},
            {"machine_id": "M-003", "utilization_pct": 80.0, "cycle_time_seconds": 50.0, "queue_length": 5},
        ]
        result = self.calculator.identify_bottleneck(machines)
        assert result["bottleneck_machine_id"] == "M-001"
        assert result["constraint_type"] == "capacity"

    def test_empty_input(self) -> None:
        """Empty machine list returns default result."""
        result = self.calculator.identify_bottleneck([])
        assert result["bottleneck_machine_id"] == ""
        assert result["constraint_type"] == "no_data"


class TestYieldOptimization:
    """Test yield optimization recommendations."""

    def setup_method(self) -> None:
        self.calculator = OEECalculator()

    def test_yield_improvement_recommendations(self) -> None:
        """Recommend parameter adjustments when yield is below target."""
        param_history = {
            "temperature": [190.0] * 20,
            "pressure": [50.0] * 20,
            "speed": [120.0] * 20,
        }
        defect_correlation = {
            "temperature": 0.6,  # strongly correlated with defects
            "pressure": -0.2,
            "speed": 0.05,
        }

        result = self.calculator.compute_yield_optimization(
            current_yield_pct=92.0,
            target_yield_pct=97.0,
            parameter_history=param_history,
            defect_correlation=defect_correlation,
        )

        assert result["current_yield_pct"] == 92.0
        assert result["target_yield_pct"] == 97.0
        assert len(result["parameter_adjustments"]) > 0
        assert result["expected_improvement_pct"] > 0.0
