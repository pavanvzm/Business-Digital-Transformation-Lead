"""Health check and metrics HTTP server for K8s probes and observability.

Endpoints:
  GET /health/live      — Liveness probe (agent process alive)
  GET /health/ready     — Readiness probe (agent ready to process)
  GET /health/startup   — Startup probe (agent fully initialized)
  GET /metrics          — Prometheus-formatted metrics

In production, serve via uvicorn for performance.
For this scaffolding, a minimal aiohttp server is used.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from config.settings import settings

logger = logging.getLogger(__name__)

try:
    from aiohttp import web
except ImportError:
    web = None  # type: ignore[assignment]
    logger.warning("aiohttp not installed — health server unavailable")


class HealthServer:
    """Lightweight async HTTP server for health checks and metrics.

    Runs on port 8000 by default. Designed for K8s probe compatibility.
    """

    def __init__(self, agent_ref: Any = None, port: int = 8000) -> None:
        self._app: Any = None
        self._runner: Any = None
        self._site: Any = None
        self._port = port
        self._agent = agent_ref
        self._startup_complete = False
        self._ready = False
        self._start_time = time.time()

        # Metrics counters
        self._metrics: dict[str, float] = {
            "messages_consumed_total": 0,
            "messages_published_total": 0,
            "po_recommendations_total": 0,
            "hitl_tickets_created_total": 0,
            "errors_total": 0,
            "cache_hits_total": 0,
            "cache_misses_total": 0,
        }

    def build_app(self) -> Any:
        """Build the aiohttp application with route handlers."""
        if web is None:
            return None

        app = web.Application()

        app.router.add_get("/health/live", self._handle_live)
        app.router.add_get("/health/ready", self._handle_ready)
        app.router.add_get("/health/startup", self._handle_startup)
        app.router.add_get("/metrics", self._handle_metrics)

        return app

    async def start(self) -> None:
        """Start the HTTP server."""
        if web is None:
            logger.warning("aiohttp not available — health server not started")
            return

        self._app = self.build_app()
        if self._app is None:
            return

        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, "0.0.0.0", self._port)
        await self._site.start()

        self._startup_complete = True
        logger.info("Health server started", port=self._port)

    async def stop(self) -> None:
        """Stop the HTTP server."""
        if self._runner:
            await self._runner.cleanup()
            logger.info("Health server stopped")

    def mark_ready(self) -> None:
        """Mark agent as ready (called after initialization completes)."""
        self._ready = True

    def increment_metric(self, name: str, value: float = 1.0) -> None:
        """Increment a metric counter."""
        if name in self._metrics:
            self._metrics[name] += value
        else:
            self._metrics[name] = value

    async def _handle_live(self, _request: Any) -> Any:
        """Liveness probe — always 200 if process is running."""
        return web.json_response(
            {"status": "alive", "uptime_seconds": round(time.time() - self._start_time)},
            status=200,
        )

    async def _handle_ready(self, _request: Any) -> Any:
        """Readiness probe — 200 if agent is ready to process messages."""
        if not self._ready:
            return web.json_response({"status": "not_ready"}, status=503)
        return web.json_response(
            {"status": "ready", "uptime_seconds": round(time.time() - self._start_time)},
            status=200,
        )

    async def _handle_startup(self, _request: Any) -> Any:
        """Startup probe — 200 once initialization is complete."""
        if not self._startup_complete:
            return web.json_response({"status": "starting"}, status=503)
        return web.json_response(
            {"status": "started", "uptime_seconds": round(time.time() - self._start_time)},
            status=200,
        )

    async def _handle_metrics(self, _request: Any) -> Any:
        """Prometheus-formatted metrics."""
        lines = [
            "# HELP mas_agent_01_messages_consumed_total Total messages consumed from Kafka",
            "# TYPE mas_agent_01_messages_consumed_total counter",
            f"mas_agent_01_messages_consumed_total {self._metrics['messages_consumed_total']:.0f}",
            "",
            "# HELP mas_agent_01_messages_published_total Total messages published to Kafka",
            "# TYPE mas_agent_01_messages_published_total counter",
            f"mas_agent_01_messages_published_total {self._metrics['messages_published_total']:.0f}",
            "",
            "# HELP mas_agent_01_po_recommendations_total Total PO recommendations generated",
            "# TYPE mas_agent_01_po_recommendations_total counter",
            f"mas_agent_01_po_recommendations_total {self._metrics['po_recommendations_total']:.0f}",
            "",
            "# HELP mas_agent_01_hitl_tickets_created_total Total HITL tickets created",
            "# TYPE mas_agent_01_hitl_tickets_created_total counter",
            f"mas_agent_01_hitl_tickets_created_total {self._metrics['hitl_tickets_created_total']:.0f}",
            "",
            "# HELP mas_agent_01_errors_total Total errors encountered",
            "# TYPE mas_agent_01_errors_total counter",
            f"mas_agent_01_errors_total {self._metrics['errors_total']:.0f}",
            "",
            "# HELP mas_agent_01_cache_hits_total Total cache hits",
            "# TYPE mas_agent_01_cache_hits_total counter",
            f"mas_agent_01_cache_hits_total {self._metrics['cache_hits_total']:.0f}",
            "",
            "# HELP mas_agent_01_cache_misses_total Total cache misses",
            "# TYPE mas_agent_01_cache_misses_total counter",
            f"mas_agent_01_cache_misses_total {self._metrics['cache_misses_total']:.0f}",
            "",
            "# HELP mas_agent_01_uptime_seconds Agent uptime in seconds",
            "# TYPE mas_agent_01_uptime_seconds gauge",
            f"mas_agent_01_uptime_seconds {round(time.time() - self._start_time)}",
            "",
        ]
        return web.Response(text="\n".join(lines), content_type="text/plain; charset=utf-8")
