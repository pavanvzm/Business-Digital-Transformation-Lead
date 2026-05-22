# 6. Sample End-to-End Workflow

> Raw Material Price Spike +20% — Full Agent Coordination Scenario

## Scenario: Copper Price Surge

**Trigger**: London Metal Exchange (LME) copper futures spike 20% in 2 hours due to supply disruption at a major Chilean mine.

**Impact radius**: 4 product lines, 127 SKUs, $2.8M monthly revenue at risk.

---

## Workflow Timeline

```
T+0min  ┌────────────────────────────────────────────────────────────────┐
        │  Agent-05 (Market Intelligence) detects price movement          │
        │  • LME copper futures: +20.2% in 2 hours                       │
        │  • News feed: "Chile mine strike — 45% of global supply"        │
        │  • Confidence: 0.97 (3 independent sources confirmed)           │
        │  • Publish: market event to Kafka topic events.market           │
        └───────────────────────────┬────────────────────────────────────┘
                                    │
T+1min  ┌───────────────────────────▼────────────────────────────────────┐
        │  Agent-01 (Procurement) receives alert                         │
        │  • Validates against internal copper inventory: 14 days supply  │
        │  • Checks alt supplier contracts: 2 pre-qualified, +8% premium  │
        │  • Calculates cost impact: +$245K/month at current consumption  │
        │  • Recommends: activate hedging, explore alt sourcing           │
        │  • Action: Semi-Autonomous — PO >$500K→ HITL required           │
        │  • Publish: price alert + recommendation to events.procurement  │
        └───────────────────────────┬────────────────────────────────────┘
                                    │
T+2min  ┌───────────────────────────▼────────────────────────────────────┐
        │  Agent-06 (Predictive Analytics) receives procurement alert     │
        │  • Triggers demand re-forecast with +20% material cost input    │
        │  • Checks demand signals from Agent-05: competitor not raising   │
        │    prices yet, Google Trends flat, sentiment neutral            │
        │  • Runs 3 scenarios:                                           │
        │    1. Pass through 50% cost → demand -8% (most likely)          │
        │    2. Pass through 100% cost → demand -15%                      │
        │    3. Absorb cost → margin -4.2%, volume flat                   │
        │  • Most likely: demand softens 8-12% next month                 │
        │  • Publish: revised forecast (↓12%) to events.forecast          │
        └───────────────────────────┬────────────────────────────────────┘
                                    │
T+3min  ┌───────────────────────────▼────────────────────────────────────┐
        │  Agent-03 (Inventory & Warehousing) receives new forecast      │
        │  • Recalculates safety stock with +20% cost: lower optimal      │
        │    buffer (cost of carrying vs. cost of stock-out)              │
        │  • Identifies: 3 SKUs with stock-out risk in 8-10 days          │
        │  • Recommends: reallocate safety stock from 5 slow-moving       │
        │    SKUs to 3 high-risk SKUs (cross-dock priority)               │
        │  • Action: Full Autonomous (within bounds) — executes           │
        │  • Publish: inventory reallocation to events.inventory          │
        └───────────────────────────┬────────────────────────────────────┘
                                    │
T+4min  ┌───────────────────────────▼────────────────────────────────────┐
        │  Agent-02 (Production & MES) receives revised forecast         │
        │  • Forecast ↓12% means 3 production batches can be deferred     │
        │  • Reschedules: moves Batches B-2041, B-2042 back 2 weeks      │
        │  • Adjusts: reallocates copper inventory to highest-margin      │
        │    product line (Product A: 38% margin vs Product B: 22%)       │
        │  • Action: Semi-Autonomous — schedule change >8h → HITL        │
        │  • Orchestrator creates HITL ticket for production manager     │
        │  • Publish: revised schedule to events.production              │
        └───────────────────────────┬────────────────────────────────────┘
                                    │
T+5min  ┌───────────────────────────▼────────────────────────────────────┐
        │  Agent-04 (Sales & Distribution) receives inventory changes    │
        │  • Available-to-promise (ATP) reduced for Product B, C         │
        │  • Checks customer tier: Tier-1 customers unaffected            │
        │  • Tier-2 customers: → reduced allocation (85% of order)       │
        │  • Recommends: 3% price increase on Product B (within HITL     │
        │    threshold — <5%) → Semi-Autonomous approved                 │
        │  • Notifies affected customers via automated communication      │
        │  • Publish: allocation plan + pricing to events.sales          │
        └───────────────────────────┬────────────────────────────────────┘
                                    │
T+6min  ┌───────────────────────────▼────────────────────────────────────┐
        │  Agent-07 (Financial & Cost Accounting) receives all inputs    │
        │  • Recalculates COGS: material cost +20% → COGS +8.4% overall   │
        │  • Gross margin impact:                                       │
        │    - Product A: 38% → 32.4% (breakeven still safe)              │
        │    - Product B: 22% → 14.8% (approaching threshold)            │
        │    - Product C: 31% → 24.1%                                    │
        │    - Product D: 45% → 41.2% (hedged contracts, delayed impact) │
        │  • Cash flow impact: +$245K monthly outflow (no hedge active)   │
        │  • P&L impact: -1.2% gross margin for product lines A-C        │
        │  • Flags: COGS variance >3% threshold → escalation             │
        │  • Publish: margin analysis + financial impact to events.finance│
        └───────────────────────────┬────────────────────────────────────┘
                                    │
T+7min  ┌───────────────────────────▼────────────────────────────────────┐
        │  Agent-08 (Compliance & Risk) reviews all actions              │
        │  • Checks: no SOX violations (segregation of duty intact)       │
        │  • Checks: pricing change <5% → no HITL violation              │
        │  • Checks: customer allocation complies with contracts          │
        │  • Flags: supply concentration risk (single mine strike)        │
        │  • Risk score: operational 7.2/10, financial 6.8/10            │
        │  • Recommends: diversify copper sourcing (geopolitical risk)   │
        │  • Publish: compliance report + risk update to events.compliance│
        └───────────────────────────┬────────────────────────────────────┘
                                    │
T+8min  ┌───────────────────────────▼────────────────────────────────────┐
        │  Agent-09 (Orchestrator & Governance) aggregates all inputs    │
        │  ┌──────────────────────────────────────────────────────────┐  │
        │  │  SITUATION SUMMARY                                        │  │
        │  │  • Trigger: LME copper +20% (Chile mine strike)           │  │
        │  │  • Forecast revised: -12% demand next month                │  │
        │  │  • Inventory: reallocated, no stock-outs expected          │  │
        │  │  • Production: 2 batches deferred, high-margin prioritized │  │
        │  │  • Pricing: +3% on Product B (within limits)              │  │
        │  │  • Margin impact: -1.2% gross margin ($98K/month)         │  │
        │  │  • Risk: supply concentration (Chile = 45% of supply)     │  │
        │  └──────────────────────────────────────────────────────────┘  │
        │                                                                  │
        │  HITL TICKETS CREATED:                                           │
        │  ┌──────────────────────────────────────────────────────────┐  │
        │  │ #H-2301: COGS variance >3% → CFO review (P1)            │  │
        │  │ #H-2302: Production schedule override → Ops Mgr (P2)    │  │
        │  │ #H-2303: Alternative supplier onboarding → CPO (P2)     │  │
        │  └──────────────────────────────────────────────────────────┘  │
        │                                                                  │
        │  3 MITIGATION OPTIONS FOR CFO:                                   │
        │  Option A: Hedge 60% copper needs at current forward price       │
        │            → Cost: $12K/month premium, preserves margin          │
        │  Option B: Pass through 50% cost increase to customers           │
        │            → Revenue impact: -8% volume, margin +2.1%            │
        │  Option C: Absorb + optimize (current path)                     │
        │            → Margin impact: -1.2%, volume flat                   │
        └─────────────────────────────────────────────────────────────────┘
```

---

## CFO Dashboard Notification

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ⚠️ CRITICAL ALERT: Raw Material Price Spike                           │
│                                                                          │
│  Material:  Copper C11000                          Priority: P1-Critical │
│  Spike:     +20.2% in 2 hours                      Ticket: #H-2301       │
│  Source:    LME / Bloomberg / S&P Global (3/3 verified)                  │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  BUSINESS IMPACT                                                     │ │
│  │  • Monthly cost increase: $245K (at current consumption)             │ │
│  │  • Margin impact: -1.2% gross (-$98K EBITDA/month)                   │ │
│  │  • Affected lines: Product A (38%→32.4%), B (22%→14.8%), C (31%→24%)│ │
│  │  • Cash flow impact: +$245K monthly outflow                          │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  RECOMMENDED ACTIONS                                                 │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  │  ☐ Option A: Hedge 60% at $9.12/kg forward                     │ │
│  │  │    → $12K/month premium. Preserves margin at current levels.    │ │
│  │  │    → Confidence: 0.85 (if strike resolves within 30 days)       │ │
│  │  │    → Approval needed: CFO                                       │ │
│  │  ├─────────────────────────────────────────────────────────────────┤ │
│  │  │  ☐ Option B: Pass through 50% cost increase (+10% price)       │ │
│  │  │    → Revenue impact: -8% volume est., margin improves +2.1%     │ │
│  │  │    → HITL required: pricing change >5%                          │ │
│  │  │    → Approval needed: Pricing Committee                         │ │
│  │  ├─────────────────────────────────────────────────────────────────┤ │
│  │  │  ☐ Option C: Absorb + optimize (current autonomous path)       │ │
│  │  │    → Margin impact: -1.2%, volume flat                          │ │
│  │  │    → No HITL required (within current bounds)                   │ │
│  │  │    → Monitor: revisit in 7 days if strike continues             │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  APPROVAL: [Approve A] [Approve B] [Approve C] [Custom] [Escalate]      │
│                                                                          │
│  ⏱ SLA: 4 hours remaining            Response rate: 72% within SLA      │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Observations from Workflow

| Aspect | Demonstration Value |
|--------|-------------------|
| **Autonomous orchestration** | 8 agents coordinated within 8 minutes without human intervention |
| **HITL gates** | 3 escalation tickets created automatically for human decisions |
| **Deterministic financials** | Agent-07 calculations are rule-based, auditable, replicable |
| **Confidence scoring** | Every recommendation includes confidence, data sources, business impact |
| **Explainable outputs** | All alternatives presented with trade-offs and reasoning |
| **Conflict avoidance** | Agent-09 detects no agent conflicts; all recommendations align |
| **Fallback readiness** | If any agent failed, fallback behavior defined per agent spec |
| **Compliance monitoring** | Agent-08 reviews all actions for regulatory compliance in real-time |

## Workflow Patterns

### Sequential Dependencies
```
Agent-05 → Agent-01 → Agent-06 → Agent-03 → Agent-02 → Agent-04
                                                              ↓
                                  Agent-08 ← Agent-07 ← Agent-04
                                      ↓
                                  Agent-09 (aggregates all)
```

### Parallel Actions
```
Agent-06 (forecast revision) runs in parallel with:
  • Agent-01 (supplier outreach)
  • Agent-03 (inventory check)

Agent-07 (cost calculation) runs in parallel with:
  • Agent-02 (production reschedule)
  • Agent-04 (pricing recommendations)
```

### Eventual Consistency
```
All agents eventually converge within 8 minutes
Maximum clock skew: <500ms (Kafka timestamp + OpenTelemetry trace)
Automatic reconciliation: Agent-09 validates all outputs are consistent
```

---

*See also: [Agent Responsibility Matrix](./02-agent-responsibility-matrix.md) | [Governance: Conflict Resolution](../governance/conflict-resolution.md)*
