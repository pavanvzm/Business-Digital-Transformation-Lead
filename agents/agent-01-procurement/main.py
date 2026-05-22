#!/usr/bin/env python3
"""CLI entry point for Agent-01 (Procurement Agent).

Usage:
    python main.py [--mode serve|evaluate|inspect|validate]
    python main.py --mode evaluate --vendor_id V001 --material steel
    python main.py --mode inspect --ticket <ticket_id>

Modes:
    serve       Start the full agent (Kafka consumer loop)
    evaluate    Run one-shot vendor evaluation
    inspect     Inspect a HITL ticket status
    validate    Run config validation and connectivity checks
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import signal
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import settings
from src.agent import ProcurementAgent
from src.scoring.vendor_scorer import VendorScorer, MaterialCategory

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
        description="Manufacturing MAS - Procurement Agent (Agent-01)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py --mode serve\n"
            "  python main.py --mode evaluate --vendor-id V001 --vendor-name 'Acme Corp' \\\n"
            "    --metrics '{\"Price Competitiveness\": 85, \"Quality Rating\": 92}'\n"
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
    parser.add_argument(
        "--vendor-id",
        type=str,
        help="Vendor ID for evaluate mode",
    )
    parser.add_argument(
        "--vendor-name",
        type=str,
        help="Vendor name for evaluate mode",
    )
    parser.add_argument(
        "--metrics",
        type=str,
        help='JSON string of metric scores, e.g. \'{"Price Competitiveness": 85}\'',
    )
    parser.add_argument(
        "--category",
        type=str,
        choices=["general", "critical_raw_materials", "commodity_materials", "packaging"],
        default="general",
        help="Material category for scoring (default: general)",
    )
    parser.add_argument(
        "--ticket",
        type=str,
        help="HITL ticket ID for inspect mode",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    return parser.parse_args()


async def run_serve_mode() -> None:
    """Run the full procurement agent in serve mode.

    Starts both the agent and the health HTTP server (for K8s probes and metrics).
    """
    agent = ProcurementAgent()
    health_server = None

    # Start health/HTTP server (optional — only if aiohttp is available)
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
            "Procurement Agent running in serve mode",
            environment=settings.environment,
        )

        # Register signal handlers on the event loop (Unix only)
        loop = asyncio.get_running_loop()
        try:
            loop.add_signal_handler(signal.SIGINT, agent._shutdown_event.set)
            loop.add_signal_handler(signal.SIGTERM, agent._shutdown_event.set)
        except (NotImplementedError, AttributeError):
            # Windows or non-UNIX — attach to asyncio.shield instead
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
    """Run one-shot vendor evaluation."""
    if not args.vendor_id or not args.vendor_name or not args.metrics:
        print("ERROR: --vendor-id, --vendor-name, and --metrics are required in evaluate mode")
        sys.exit(1)

    try:
        metric_scores = json.loads(args.metrics)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in --metrics: {e}")
        sys.exit(1)

    category_map = {
        "general": MaterialCategory.GENERAL,
        "critical_raw_materials": MaterialCategory.CRITICAL_RAW,
        "commodity_materials": MaterialCategory.COMMODITY,
        "packaging": MaterialCategory.PACKAGING,
    }
    category = category_map.get(args.category, MaterialCategory.GENERAL)

    scorer = VendorScorer()
    scorecard = scorer.compute_scorecard(
        vendor_id=args.vendor_id,
        vendor_name=args.vendor_name,
        metric_scores=metric_scores,
        category=category,
    )

    print(f"\n{'='*60}")
    print(f"VENDOR SCORECARD: {args.vendor_name} ({args.vendor_id})")
    print(f"{'='*60}")
    print(f"Period:       {scorecard.period}")
    print(f"Category:     {scorecard.category.value}")
    print(f"Overall:      {scorecard.overall_score}/100")
    print(f"Trend:        {scorecard.trend}")
    print(f"Confidence:   {scorecard.confidence:.0%}")
    print(f"Risk Flags:   {'; '.join(scorecard.risk_flags) if scorecard.risk_flags else 'None'}")
    print(f"\n{'─'*60}")
    print(f"{'Metric':<30} {'Score':>8} {'Weight':>8} {'Source':<20}")
    print(f"{'─'*60}")
    for metric in scorecard.metrics:
        print(f"{metric.name:<30} {metric.score:>8.1f} {metric.weight:>8.2f} {metric.data_source:<20}")
    print(f"{'─'*60}\n")

    # HITL check
    if scorecard.overall_score < 60:
        print("⚠️  HITL REQUIRED: Score below minimum acceptable threshold (60/100)")
    if scorecard.overall_score < 70:
        print("⚠️  HITL REQUIRED: Score below quality critical threshold (70/100)")


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
    print(f"CONFIGURATION VALIDATION")
    print(f"{'='*60}")

    # Agent config
    print(f"\nAgent: {settings.agent_id} v{settings.agent_version}")
    print(f"Environment: {settings.environment}")
    print(f"Log level: {settings.log_level}")
    print(f"Autonomy: {settings.load_config_file().get('agent', {}).get('autonomy_level', 'unknown')}")

    # Kafka config
    print(f"\nKafka: {settings.kafka.bootstrap_servers}")
    print(f"  Consumer group: {settings.kafka.consumer_group_id}")
    print(f"  Subscribed topics:")
    print(f"    → {settings.kafka.topic_market_events}")
    print(f"    → {settings.kafka.topic_forecast_events}")
    print(f"    → {settings.kafka.topic_inventory_events}")
    print(f"    → {settings.kafka.topic_orchestrator_events}")
    print(f"  Produces to:")
    print(f"    → {settings.kafka.topic_procurement_events}")
    print(f"    → {settings.kafka.topic_dead_letter}")

    # Scoring config
    print(f"\nScoring:")
    print(f"  Min acceptable score: {settings.scoring.min_acceptable_score}")
    print(f"  Quality critical: {settings.scoring.quality_critical_threshold}%")
    print(f"  Price spike warning: {settings.scoring.price_spike_warning_pct}%")
    print(f"  Price spike critical: {settings.scoring.price_spike_critical_pct}%")
    print(f"  PO HITL threshold: ${settings.scoring.po_value_hitl_threshold_usd:,.0f}")

    # Database
    print(f"\nPostgreSQL: {settings.database.postgres_dsn.split('@')[-1] if '@' in settings.database.postgres_dsn else 'not configured'}")
    print(f"Redis: {settings.database.redis_url}")

    # HITL
    print(f"\nHITL:")
    print(f"  Poll interval: {settings.hitl_poll_interval_seconds}s")
    print(f"  Default timeout: {settings.hitl_timeout_seconds}s")

    # Fallback
    print(f"\nFallback:")
    print(f"  Price buffer: {settings.fallback_price_buffer_pct}%")
    print(f"  Forecast window: {settings.fallback_forecast_months} months")

    # YAML config
    yaml_config = settings.load_config_file()
    material_cats = yaml_config.get("scoring", {}).get("material_categories", {})
    print(f"\nMaterial categories: {list(material_cats.keys())}")
    print(f"Escalation paths: {len(yaml_config.get('escalation', {}).get('paths', []))}")

    print(f"\n{'='*60}")
    print(f"VALIDATION COMPLETE — All settings loaded successfully")
    print(f"{'='*60}\n")


async def main() -> None:
    """Main entry point."""
    args = parse_args()
    setup_logging(args.log_level)

    logger.info("Procurement Agent CLI", mode=args.mode, version=settings.agent_version)

    mode_handlers = {
        "serve": run_serve_mode,
        "evaluate": run_evaluate_mode,
        "inspect": run_inspect_mode,
        "validate": run_validate_mode,
    }

    handler = mode_handlers[args.mode]
    if args.mode == "evaluate":
        await handler(args)
    elif args.mode == "inspect":
        await handler(args)
    else:
        await handler()


if __name__ == "__main__":
    asyncio.run(main())
