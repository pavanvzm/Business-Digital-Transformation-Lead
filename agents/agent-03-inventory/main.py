#!/usr/bin/env python3
"""CLI entry point for Agent-03 (Inventory & Warehousing Agent).

Usage:
    python main.py [--mode serve|validate|inspect]
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import settings
from src.agent import InventoryAgent

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manufacturing MAS - Inventory & Warehousing Agent (Agent-03)",
    )
    parser.add_argument(
        "--mode",
        choices=["serve", "validate", "inspect"],
        default="serve",
    )
    parser.add_argument("--ticket", type=str, help="HITL ticket ID for inspect mode")
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
    )
    return parser.parse_args()


async def run_serve_mode() -> None:
    agent = InventoryAgent()
    await agent.start()
    logger.info("Inventory Agent running in serve mode")
    try:
        await agent.run()
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Shutdown signal received")
    finally:
        await agent.shutdown()


async def run_validate_mode() -> None:
    print(f"\n{'='*60}")
    print(f"CONFIGURATION VALIDATION — Agent-03 Inventory & Warehousing")
    print(f"{'='*60}")
    yaml_config = settings.load_config_file()
    print(f"\nAgent: {settings.agent_id} v{settings.agent_version}")
    print(f"Environment: {settings.environment}")
    print(f"Autonomy: {yaml_config.get('agent', {}).get('autonomy_level', 'unknown')}")
    print(f"\nKafka: {settings.kafka.bootstrap_servers}")
    print(f"  Consumer group: {settings.kafka.consumer_group_id}")
    print(f"\nInventory Settings:")
    print(f"  Service level: {settings.inventory.service_level_pct}%")
    print(f"  Dead stock threshold: {settings.inventory.dead_stock_days} days")
    print(f"  Space util critical: {settings.inventory.space_utilization_critical_pct}%")
    print(f"  Stock-out HITL threshold: {settings.inventory.stock_out_probability_hitl:.0%}")
    print(f"\nHITL:")
    print(f"  Poll interval: {settings.hitl_poll_interval_seconds}s")
    print(f"  Timeout: {settings.hitl_timeout_seconds}s")
    print(f"\nEscalation paths: {len(yaml_config.get('escalation', {}).get('paths', []))}")
    print(f"\n{'='*60}")
    print(f"VALIDATION COMPLETE")
    print(f"{'='*60}\n")


async def run_inspect_mode(args: argparse.Namespace) -> None:
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
    print(f"\nAudit Log:")
    for entry in ticket.audit_log:
        print(f"  [{entry['timestamp']}] {entry['actor']}: {entry['detail']}")


async def main() -> None:
    args = parse_args()
    setup_logging(args.log_level)
    logger.info("Inventory Agent CLI", mode=args.mode)

    if args.mode == "serve":
        await run_serve_mode()
    elif args.mode == "validate":
        await run_validate_mode()
    elif args.mode == "inspect":
        await run_inspect_mode(args)


if __name__ == "__main__":
    asyncio.run(main())
