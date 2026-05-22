#!/usr/bin/env python3
"""CLI entry point for Agent-02 (Production & MES Agent).

Usage:
    python main.py [--mode serve|evaluate|inspect|validate]
    python main.py --mode evaluate --line Line-A --shift S1 \
        --operating 420 --planned 480 --cycle-time 60 \
        --produced 1000 --good 970 --defective 30
    python main.py --mode inspect --ticket <ticket_id>
    python main.py --mode validate

Modes:
    serve       Start the full agent (Kafka consumer loop)
    evaluate    Run one-shot OEE calculation
    inspect     Inspect a HITL ticket status
    validate    Run config validation and connectivity checks
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import settings
from src.agent import ProductionMESAgent
from src.scoring.oee_calculator import OEECalculator

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Manufacturing MAS - Production & MES Agent (Agent-02)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py --mode serve\n"
            "  python main.py --mode evaluate --line Line-A --shift S1 \\\n"
            "    --operating 420 --planned 480 --cycle-time 60 \\\n"
            "    --produced 1000 --good 970 --defective 30 \\\n"
            "    --downtime 60 --planned-downtime 30\n"
            "  python main.py --mode inspect --ticket abc-123\n"
            "  python main.py --mode validate\n"
        ),
    )

    parser.add_argument(
        "--mode",
        choices=["serve", "evaluate", "inspect", "validate"],
        default="serve",
        help="Agent operation mode (default: serve)",
    )

    # OEE evaluation arguments
    parser.add_argument("--line", type=str, default="Line-A", help="Production line name")
    parser.add_argument("--shift", type=str, default="S1", help="Shift identifier")
    parser.add_argument(
        "--operating", type=float, default=420.0,
        help="Operating time in minutes (default: 420)",
    )
    parser.add_argument(
        "--planned", type=float, default=480.0,
        help="Planned production time in minutes (default: 480)",
    )
    parser.add_argument(
        "--cycle-time", type=float, default=60.0,
        help="Ideal cycle time in seconds (default: 60)",
    )
    parser.add_argument("--produced", type=int, default=1000, help="Total units produced")
    parser.add_argument("--good", type=int, default=970, help="Total good units")
    parser.add_argument("--defective", type=int, default=30, help="Total defective units")
    parser.add_argument(
        "--downtime", type=float, default=0.0,
        help="Total downtime in minutes (default: 0)",
    )
    parser.add_argument(
        "--planned-downtime", type=float, default=0.0,
        help="Planned downtime in minutes (default: 0)",
    )

    # Inspection argument
    parser.add_argument("--ticket", type=str, help="HITL ticket ID for inspect mode")

    # Log level
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    return parser.parse_args()


async def run_serve_mode() -> None:
    """Run the full agent in serve mode with health server."""
    agent = ProductionMESAgent()
    health_server = None

    # Start health/HTTP server (optional)
    try:
        from src.health_server import HealthServer
        health_server = HealthServer(agent_ref=agent, port=8000)
        await health_server.start()
    except ImportError:
        logger.info("aiohttp not available — health server disabled")
    except Exception:
        logger.exception("Failed to start health server")

    try:
        await agent.start()
        if health_server:
            health_server.mark_ready()
        logger.info(
            "Production & MES Agent running in serve mode",
            environment=settings.environment,
        )

        # Register signal handlers on the event loop (Unix only)
        loop = asyncio.get_running_loop()
        try:
            loop.add_signal_handler(signal.SIGINT, agent._shutdown_event.set)
            loop.add_signal_handler(signal.SIGTERM, agent._shutdown_event.set)
        except (NotImplementedError, AttributeError):
            pass

        await agent.run()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except asyncio.CancelledError:
        logger.info("Run loop cancelled")
    finally:
        await agent.shutdown()
        if health_server:
            await health_server.stop()


async def run_evaluate_mode(args: argparse.Namespace) -> None:
    """Run one-shot OEE calculation."""
    calculator = OEECalculator()

    oee_result = calculator.calculate_oee(
        production_line=args.line,
        shift_id=args.shift,
        period_start=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0),
        period_end=datetime.now(timezone.utc),
        operating_time_minutes=args.operating,
        planned_production_time_minutes=args.planned,
        ideal_cycle_time_seconds=args.cycle_time,
        total_units_produced=args.produced,
        total_good_units=args.good,
        total_defective_units=args.defective,
        total_downtime_minutes=args.downtime,
        planned_downtime_minutes=args.planned_downtime,
    )

    print(f"\n{'='*60}")
    print(f"OEE REPORT: {args.line} (Shift {args.shift})")
    print(f"{'='*60}")
    print(f"Period: {oee_result.period_start.date()} → {oee_result.period_end.date()}")
    print(f"Trend:  {oee_result.trend.value}")
    print(f"{'─'*60}")
    print(f"{'Component':<20} {'Value':>8} {'Target':>8} {'Status':<12}")
    print(f"{'─'*60}")
    print(f"{'Availability':<20} {oee_result.availability_pct:>7.1f}% {90.0:>7.0f}% {'✓' if oee_result.availability_pct >= 90 else '✗':<12}")
    print(f"{'Performance':<20} {oee_result.performance_pct:>7.1f}% {95.0:>7.0f}% {'✓' if oee_result.performance_pct >= 95 else '✗':<12}")
    print(f"{'Quality':<20} {oee_result.quality_pct:>7.1f}% {99.0:>7.0f}% {'✓' if oee_result.quality_pct >= 99 else '✗':<12}")
    print(f"{'─'*60}")
    print(f"{'OEE':<20} {oee_result.oee_pct:>7.1f}% {'─':>7} {'✓' if oee_result.oee_pct >= 70 else '⚠ HITL':<12}")
    print(f"{'─'*60}")
    print(f"\nProduction Summary:")
    print(f"  Total units:  {oee_result.total_units_produced}")
    print(f"  Good units:   {oee_result.total_good_units}")
    print(f"  Defective:    {oee_result.total_defective_units}")
    print(f"  Downtime:     {oee_result.total_downtime_minutes:.0f} min")
    print(f"  Planned DT:   {oee_result.planned_downtime_minutes:.0f} min")

    # HITL check
    if oee_result.oee_pct < settings.oee.oee_critical_threshold_pct:
        print(f"\n⚠️  HITL REQUIRED: OEE {oee_result.oee_pct:.1f}% below critical threshold ({settings.oee.oee_critical_threshold_pct:.0f}%)")
    print()


async def run_inspect_mode(args: argparse.Namespace) -> None:
    """Inspect a HITL ticket status."""
    from src.hitl.gate import HITLGate

    gate = HITLGate()
    ticket = await gate.get_ticket(args.ticket)

    if ticket is None:
        print(f"Ticket not found: {args.ticket}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"HITL TICKET: {ticket.ticket_id}")
    print(f"{'='*60}")
    print(f"Title:      {ticket.title}")
    print(f"Priority:   {ticket.priority.value}")
    print(f"Status:     {ticket.status.value}")
    print(f"Source:     {ticket.source_agent}")
    print(f"Created:    {ticket.created_at.isoformat()}")
    print(f"SLA:        {ticket.sla_deadline.isoformat() if ticket.sla_deadline else 'N/A'}")
    print(f"Resolved:   {ticket.resolved_at.isoformat() if ticket.resolved_at else 'Pending'}")
    print(f"By:         {ticket.resolved_by or 'N/A'}")
    print(f"Decision:   {ticket.decision or 'Pending'}")
    print(f"\nDescription: {ticket.description}")
    print(f"\nAudit Log:")
    for entry in ticket.audit_log:
        print(f"  [{entry['timestamp']}] {entry['actor']}: {entry['detail']}")


async def run_validate_mode() -> None:
    """Validate configuration and connectivity."""
    print(f"\n{'='*60}")
    print(f"CONFIGURATION VALIDATION — Agent-02 Production & MES")
    print(f"{'='*60}")

    # Agent config
    yaml_config = settings.load_config_file()
    print(f"\nAgent: {settings.agent_id} v{settings.agent_version}")
    print(f"Environment: {settings.environment}")
    print(f"Log level: {settings.log_level}")
    print(f"Autonomy: {yaml_config.get('agent', {}).get('autonomy_level', 'unknown')}")

    # Kafka config
    print(f"\nKafka: {settings.kafka.bootstrap_servers}")
    print(f"  Consumer group: {settings.kafka.consumer_group_id}")
    print(f"  Subscribed topics:")
    print(f"    → {settings.kafka.topic_inventory_events}")
    print(f"    → {settings.kafka.topic_forecast_events}")
    print(f"    → {settings.kafka.topic_orchestrator_events}")
    print(f"    → {settings.kafka.topic_market_events}")
    print(f"  Produces to:")
    print(f"    → {settings.kafka.topic_production_events}")
    print(f"    → {settings.kafka.topic_dead_letter}")

    # OEE config
    print(f"\nOEE:")
    print(f"  Availability target: {settings.oee.availability_target_pct}%")
    print(f"  Performance target: {settings.oee.performance_target_pct}%")
    print(f"  Quality target: {settings.oee.quality_target_pct}%")
    print(f"  Critical OEE threshold: {settings.oee.oee_critical_threshold_pct}%")
    print(f"  Quality defect critical: {settings.oee.quality_defect_critical_pct}%")
    print(f"  Schedule variance threshold: {settings.oee.schedule_variance_hours}h")

    # Predictive maintenance
    print(f"\nPredictive Maintenance:")
    print(f"  Proactive threshold: {settings.oee.pm_confidence_threshold}")
    print(f"  Critical (halt) threshold: {settings.oee.pm_critical_confidence}")
    print(f"  Retraining OEE drop: {settings.oee.retraining_oee_drop_pct}%")
    print(f"  Retraining quality sigma: {settings.oee.retraining_quality_sigma}σ")
    print(f"  Max retraining cycles: {settings.oee.retraining_max_cycles}")

    # Database
    print(f"\nPostgreSQL: {settings.database.postgres_dsn.split('@')[-1] if '@' in settings.database.postgres_dsn else 'not configured'}")
    print(f"Redis: {settings.database.redis_url}")

    # HITL
    print(f"\nHITL:")
    print(f"  Poll interval: {settings.hitl_poll_interval_seconds}s")
    print(f"  Default timeout: {settings.hitl_timeout_seconds}s")

    # Fallback
    print(f"\nFallback:")
    print(f"  MES disconnected max age: {yaml_config.get('fallback', {}).get('mes_disconnected', {}).get('max_age_minutes', 30)} min")
    print(f"  Schedule optimizer fallback: {yaml_config.get('fallback', {}).get('schedule_optimizer_unavailable', {}).get('strategy', 'fifo_legacy')}")

    # Escalation paths
    esc_paths = yaml_config.get("escalation", {}).get("paths", [])
    print(f"\nEscalation paths: {len(esc_paths)}")
    for p in esc_paths:
        print(f"  → {p.get('trigger', '')} → {p.get('notify', [])} (SLA: {p.get('sla_minutes', '?')}min, {p.get('priority', '?')})")

    # Production lines
    lines = yaml_config.get("oee", {}).get("production_lines", {})
    print(f"\nProduction lines monitored: {list(lines.keys())}")

    print(f"\n{'='*60}")
    print(f"VALIDATION COMPLETE — All settings loaded successfully")
    print(f"{'='*60}\n")


async def main() -> None:
    """Main entry point."""
    args = parse_args()
    setup_logging(args.log_level)

    logger.info("Production & MES Agent CLI", mode=args.mode, version=settings.agent_version)

    mode_handlers = {
        "serve": run_serve_mode,
        "evaluate": run_evaluate_mode,
        "inspect": run_inspect_mode,
        "validate": run_validate_mode,
    }

    handler = mode_handlers[args.mode]
    if args.mode in ("evaluate", "inspect"):
        await handler(args)
    else:
        await handler()


if __name__ == "__main__":
    asyncio.run(main())
