#!/bin/bash
# =============================================================================
# Manufacturing MAS — Agent-01 Procurement: Container Entrypoint
#
# Environment variable substitution for config files + agent startup.
# Supports low-connectivity fallback: agent runs even if Kafka/DB are down.
# =============================================================================

set -euo pipefail

echo "================================================"
echo "  Manufacturing MAS — Agent-01 Procurement"
echo "  Version: ${AGENT_VERSION:-1.0.0}"
echo "  Environment: ${ENVIRONMENT:-development}"
echo "================================================"

# ── Step 1: Wait for dependencies (with timeout) ──
# Use a non-blocking approach — agent handles connection failures internally
MAX_WAIT=30
COUNTER=0

if [ -n "${DB_POSTGRES_DSN:-}" ]; then
    echo "=> PostgreSQL will be connected by the agent (async)"
fi

if [ -n "${DB_REDIS_URL:-}" ]; then
    echo "=> Redis will be connected by the agent (async)"
fi

if [ -n "${KAFKA_BOOTSTRAP_SERVERS:-}" ]; then
    echo "=> Kafka bootstrap: ${KAFKA_BOOTSTRAP_SERVERS}"
fi

# ── Step 2: Create required directories ──
mkdir -p /var/agent-01/queue /var/log/agent-01

# ── Step 3: Start agent ──
echo "=> Starting Procurement Agent..."
exec python main.py --mode serve --log-level "${LOG_LEVEL:-INFO}"
