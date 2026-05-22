# Governance: Autonomy Levels

> Three-tier autonomy framework with circuit breaker architecture

## Autonomy Level Definitions

| Level | Code | Name | Description | Human Role | Default for Agents |
|-------|------|------|-------------|-----------|-------------------|
| 1 | L1 | Advisory | Agent analyzes, recommends, and presents options with reasoning | Required for all actions | Agent-05, Agent-06 |
| 2 | L2 | Semi-Autonomous | Agent executes within defined policy bounds; escalates when thresholds exceeded | Monitor with override capability; mandatory for defined actions | Agent-01, Agent-02, Agent-04, Agent-07 |
| 3 | L3 | Full Autonomous | Agent executes fully within bounds; only escalates on errors or conflicts | Exception-only monitoring | Agent-03, Agent-08, Agent-09 |

## Phase-Based Autonomy Assignment

| Agent | Phase 1 (0-3mo) | Phase 2 (3-6mo) | Phase 3 (6-12mo) |
|-------|-----------------|-----------------|-------------------|
| Agent-01 Procurement | L1 (Advisory) | L2 (Semi-Autonomous) | L2 (Semi-Autonomous) |
| Agent-02 Production | L1 (Advisory) | L1 → L2 (month 5) | L2 (Semi-Autonomous) |
| Agent-03 Inventory | L1 (Advisory) | L2 (Semi-Autonomous) | L3 (Full Autonomous) |
| Agent-04 Sales | L1 (Advisory) | L2 (Semi-Autonomous) | L2 (Semi-Autonomous) |
| Agent-05 Market | L1 (Advisory) | L1 (Advisory) | L2 (Semi-Autonomous) |
| Agent-06 Predictive | L1 (Advisory) | L1 (Advisory) | L1 (Advisory) |
| Agent-07 Financial | L1 (Read-only) | L2 (Semi-Autonomous) | L2 (Semi-Autonomous) |
| Agent-08 Compliance | L1 (Monitor) | L3 (Full Autonomous) | L3 (Full Autonomous) |
| Agent-09 Orchestrator | L2 (Semi-Autonomous) | L3 (Full Autonomous) | L3 (Full Autonomous) |

## Circuit Breaker States

```
┌─────────────────────────────────────────────────────────────┐
│                   CIRCUIT BREAKER STATES                     │
│                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌──────────────┐  │
│  │   CLOSED    │────▶│    OPEN     │────▶│  HALF-OPEN   │  │
│  │ (Normal op) │     │ (Tripped)   │     │ (Testing)    │  │
│  └─────────────┘     └─────────────┘     └──────────────┘  │
│        │                                                    │
│        │ All metrics within threshold                        │
│        │ Agent operates at assigned autonomy level           │
│        │                                                    │
│  ┌─────┴─────────────────────────────────────────────────┐  │
│  │ TRIGGER CONDITIONS TO OPEN:                            │  │
│  │ • KPI threshold breached (e.g., forecast MAPE >25%)   │  │
│  │ • Consecutive errors >5 in 10 minutes                  │  │
│  │ • Latency >5s for critical path                        │  │
│  │ • Data quality score <80%                              │  │
│  │ • Compliance violation detected by Agent-08            │  │
│  │ • Agent conflict unresolved after 2 arbitration rounds │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                             │
│  WHEN OPEN:                                                 │
│  • Agent reverts to L1 (Advisory) immediately               │
│  • All pending actions placed in HITL queue                 │
│  • Orchestrator notified with full context                  │
│  • Root cause investigation auto-triggered                  │
│                                                             │
│  WHEN HALF-OPEN (after 15 min timeout):                    │
│  • Agent processes 5 test transactions                      │
│  • If all pass → CLOSED (resume normal autonomy)            │
│  • If any fail → OPEN (extended investigation)              │
└─────────────────────────────────────────────────────────────┘
```
