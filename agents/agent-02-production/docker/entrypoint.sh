#!/bin/bash
# =============================================================================
# Manufacturing MAS — Agent-02 Production & MES: Container Entrypoint
# Supports low-connectivity fallback: agent runs even if Kafka/DB are down.
# =============================================================================

set -euo pipefail

echo "================================================"
echo "  Manufacturing MAS — Agent-02 Production & MES"
echo "  Version: ${AGENT_VERSION:-1.0.0}"
echo "  Environment: ${ENVIRONMENT:-development}"
echo "================================================"

# ── Step 1: Create required directories ──
mkdir -p /var/agent-02/queue /var/log/agent-02

# ── Step 2: Start agent ──
echo "=> Starting Production & MES Agent..."
exec python main.py --mode serve --log-level "${LOG_LEVEL:-INFO}"
