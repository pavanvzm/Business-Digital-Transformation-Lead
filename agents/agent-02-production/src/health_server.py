"""Lightweight HTTP health server for Kubernetes probes and Prometheus metrics.

Provides:
- /health/live — Liveness probe (agent process alive)
- /health/ready — Readiness probe (agent connected to dependencies)
- /metrics — Prometheus metrics endpoint
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class HealthServer:
    """HTTP health server using aiohttp (optional dependency).

    Gracefully degrades to no-op if aiohttp is not installed.
    """

    def __init__(
        self,
        agent_ref: Any = None,
        host: str = "0.0.0.0",
        port: int = 8000,
    ) -> None:
        self.agent = agent_ref
        self.host = host
        self.port = port
        self._app: Any = None
        self._runner: Any = None
        self._site: Any = None
        self._ready = False
        self._started = False

    async def start(self) -> None:
        """Start the HTTP server."""
        try:
            from aiohttp import web  # type: ignore[import-untyped]

            self._app = web.Application()

            # Register routes
            self._app.router.add_get("/health/live", self._handle_liveness)
            self._app.router.add_get("/health/ready", self._handle_readiness)
            self._app.router.add_get("/health", self._handle_health)
            self._app.router.add_get("/metrics", self._handle_metrics)
            self._app.router.add_get("/", self._handle_root)

            self._runner = web.AppRunner(self._app)
            await self._runner.setup()
            self._site = web.TCPSite(self._runner, self.host, self.port)
            await self._site.start()
            self._started = True

            logger.info("Health server started", host=self.host, port=self.port)
        except ImportError:
            logger.info("aiohttp not available — health server disabled")
        except Exception:
            logger.exception("Failed to start health server")

    async def stop(self) -> None:
        """Stop the HTTP server."""
        if self._runner:
            await self._runner.cleanup()
            self._started = False
            logger.info("Health server stopped")

    def mark_ready(self) -> None:
        """Mark the agent as ready (for readiness probe)."""
        self._ready = True

    async def _handle_liveness(self, request: Any) -> Any:
        """Liveness probe — agent process is alive."""
        from aiohttp import web
        return web.json_response({"status": "alive", "agent": "agent-02"})

    async def _handle_readiness(self, request: Any) -> Any:
        """Readiness probe — agent is ready to serve."""
        from aiohttp import web
        if not self._ready or not self.agent:
            return web.json_response(
                {"status": "not_ready", "agent": "agent-02"},
                status=503,
            )
        return web.json_response({
            "status": "ready",
            "agent": "agent-02",
            "environment": getattr(self.agent.settings, "environment", "unknown"),
        })

    async def _handle_health(self, request: Any) -> Any:
        """Detailed health endpoint with agent state."""
        from aiohttp import web
        if not self.agent:
            return web.json_response({"status": "no_agent"}, status=503)

        health_data = await self.agent.get_health()
        return web.json_response({
            **health_data,
            "agent_id": "agent-02",
            "agent_version": getattr(self.agent.settings, "agent_version", "unknown"),
            "ready": self._ready,
        })

    async def _handle_metrics(self, request: Any) -> Any:
        """Prometheus metrics endpoint."""
        from aiohttp import web

        if not self.agent:
            metrics = "# agent-02 metrics unavailable\n"
        else:
            state = self.agent.state
            metrics_lines = [
                "# HELP agent_messages_consumed Total messages consumed",
                "# TYPE agent_messages_consumed counter",
                f"agent_messages_consumed {state.total_messages_consumed}",
                "",
                "# HELP agent_messages_published Total messages published",
                "# TYPE agent_messages_published counter",
                f"agent_messages_published {state.total_published}",
                "",
                "# HELP agent_oee_reports Total OEE reports generated",
                "# TYPE agent_oee_reports counter",
                f"agent_oee_reports {state.total_oee_reports}",
                "",
                "# HELP agent_quality_alerts Total quality alerts raised",
                "# TYPE agent_quality_alerts counter",
                f"agent_quality_alerts {state.total_quality_alerts}",
                "",
                "# HELP agent_maintenance_triggers Total maintenance triggers",
                "# TYPE agent_maintenance_triggers counter",
                f"agent_maintenance_triggers {state.total_maintenance_triggers}",
                "",
                "# HELP agent_errors Total errors encountered",
                "# TYPE agent_errors counter",
                f"agent_errors {state.total_errors}",
                "",
                "# HELP agent_active_hitl_tickets Current HITL tickets",
                "# TYPE agent_active_hitl_tickets gauge",
                f"agent_active_hitl_tickets {len(state.active_hitl_tickets)}",
                "",
                "# HELP agent_fallback_mode Fallback mode active",
                "# TYPE agent_fallback_mode gauge",
                f"agent_fallback_mode {1 if state.fallback_mode else 0}",
                "",
            ]
            # Per-line OEE metrics
            for line, oee in state.last_oee_by_line.items():
                metrics_lines.append(f"agent_oee_pct{{line=\"{line}\"}} {oee}")

            metrics = "\n".join(metrics_lines)

        return web.Response(text=metrics, content_type="text/plain; version=0.0.4")

    async def _handle_root(self, request: Any) -> Any:
        """Root endpoint — show available routes."""
        from aiohttp import web
        return web.json_response({
            "agent": "agent-02-production",
            "endpoints": {
                "/health/live": "Liveness probe",
                "/health/ready": "Readiness probe",
                "/health": "Detailed health status",
                "/metrics": "Prometheus metrics",
            },
        })
