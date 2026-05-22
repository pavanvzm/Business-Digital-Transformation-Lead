# 4. Phased Implementation Roadmap

> 12-month enterprise rollout: Visibility → Semi-Autonomous → Full Autonomous

## 4.1 Phase Overview

```
Phase 1         Phase 2              Phase 3
0-3 months      3-6 months           6-12 months
┌──────────┐    ┌──────────────┐     ┌──────────────────┐
│ Visibility │    │ Semi-Autonomous│    │ Full Autonomous   │
│ Layer      │───▶│ Optimization   │───▶│ Enterprise Rollout│
│ + Forecast │    │ + HITL Gates   │    │ + Circuit Breakers│
│ (1 product │    │ (3 product     │    │ (All lines +      │
│  line)     │    │  lines + fin.) │    │  global ops)      │
└──────────┘    └──────────────┘     └──────────────────┘
     │                  │                      │
     ▼                  ▼                      ▼
 20% forecast err    15% inventory        5-8% margin
 reduction           turnover +3%        expansion + full
                     margin improv.      SOX/ISO audit ready
```

## 4.2 Phase 1: Visibility Layer + Forecasting Pilot (Months 0-3)

### Objective
Build the data foundation and prove forecasting value on a single product line. No autonomous execution — purely advisory.

### Timeline

| Week | Milestone | Dependencies |
|------|-----------|-------------|
| 1-2 | Data infrastructure setup (Kafka, Delta Lake, MinIO, PostgreSQL) | IT infrastructure approval |
| 3-4 | ERP/MES connectors (1 product line) + data quality gates | SAP/Oracle API access |
| 5-6 | Agent-05 (Market Intelligence) — basic competitor pricing + sentiment | Web scraping licensing |
| 7-8 | Agent-06 (Predictive Analytics) — forecast model on 1 product line | 3+ years historical data |
| 9-10 | Agent-07 (Financial) — BOM costing, margin tracking (rule-based) | Cost data from ERP |
| 11 | Agent-09 (Orchestrator) — basic health monitoring dashboard | All above agents |
| 12 | Phase 1 Go/No-Go: 20% forecast error reduction validated | CPO sign-off |

### Scope
- **1 product line** with ≤50 SKUs
- **Agents deployed**: Agent-05 (advisory), Agent-06 (advisory), Agent-07 (read-only), Agent-09 (monitoring)
- **Forecast horizon**: 1 month (not 3)
- **Data sources**: ERP + POS feed + manual market data upload
- **Legacy parallel**: Full manual operations continue; system runs read-only
- **Success gate**: MAPE <18% (from current baseline) with >90% data quality pass rate

### Team Required
- 1 × Data Engineer (Kafka, Delta Lake)
- 1 × ML Engineer (forecasting models)
- 1 × Backend Engineer (agent scaffolding)
- 1 × Domain Expert (supply chain planner)
- 0.5 × DevOps (infrastructure)

### ROI Milestones
- Reduced forecast error: 20% → est. $200K inventory cost savings (1 line)
- Data quality automation: 30% reduction in manual data cleanup
- Baseline infrastructure for all subsequent phases

### Deliverables
- [x] Kafka cluster with 5 topics (events.procurement, .production, .inventory, .sales, .market)
- [x] Delta Lake bronze/silver/gold layers for 1 product line
- [x] Data quality gates (Great Expectations): 47 automated checks
- [x] Agent-05 market dashboard (Grafana)
- [x] Agent-06 forecast with MAPE tracking
- [x] Agent-07 cost dashboard (read-only)
- [x] Agent-09 system health dashboard
- [x] Dual-write reconciliation script (MAS ←→ legacy)

---

## 4.3 Phase 2: Semi-Autonomous Optimization + HITL Gates (Months 3-6)

### Objective
Extend to 3 product lines, add execution agents with human-in-the-loop gates, integrate financial engine.

### Timeline

| Week | Milestone | Dependencies |
|------|-----------|-------------|
| 13-14 | Agent-01 (Procurement) — vendor scoring, price monitoring, advisory mode | ERP PO data, market feeds |
| 15-16 | Agent-03 (Inventory) — dynamic reorder, safety stock, advisory mode | WMS integration |
| 17-18 | Agent-04 (Sales) — order routing, fulfillment optimization, HITL pricing | CRM + TMS integration |
| 19-20 | Agent-02 (Production) — MES integration, OEE tracking, scheduling | MES API access |
| 21-22 | HITL gate implementation (pricing >5%, schedule override, financial close) | Governance framework approval |
| 23-24 | Cross-agent integration: Agent-06 → Agent-01/02/03/04 forecast consumption | All agents above |
| 25-26 | Agent-08 (Compliance) — SOX controls, audit logging, risk monitoring | Legal/compliance sign-off |
| 27-28 | Phase 2 Go/No-Go: 3 product lines operational with HITL gates | CFO + COO sign-off |

### Scope
- **3 product lines** with ≤300 SKUs total
- **All 9 agents deployed**: Agents 01-04 in Semi-Autonomous (L2), Agents 05-06 Advisory (L1), Agent-07 Semi-Autonomous (L2) for deterministic costing, Agent-08 Full Autonomous (L3) for compliance monitoring, Agent-09 Full Autonomous (L3)
- **HITL gates active**: Pricing >5%, production override, supplier onboarding, financial close, compliance-critical
- **Forecast horizon**: Extended to 3 months
- **Legacy parallel**: Dual-write with reconciliation (MAS writes shadow to legacy)
- **Success gate**: Human intervention rate <20%, inventory turnover +5%

### Additional Team
- +1 × Full-Stack Developer (HITL dashboard)
- +1 × Data Engineer (additional integrations)
- +1 × MES/ERP Integration Specialist
- +1 × Compliance Officer (part-time, domain advisor)

### ROI Milestones
- Inventory turnover: +5% improvement → est. $500K working capital reduction
- OEE improvement: +3% via predictive maintenance alerts → est. $300K
- Margin: +1% via dynamic cost-to-serve (pricing optimization)
- Manual effort reduction: 20% in procurement, 15% in production planning

### HITL Gate Implementation

```
┌────────────────────────────────────────────────────────────┐
│                    HITL GATE PROXY                          │
│                                                            │
│  Agent Decision ──→ Threshold Check ──→ Within Bounds?     │
│       │                  │                  │              │
│       │                  │                  ├── Yes ──→    │
│       │                  │                  │    Execute   │
│       │                  ▼                  │              │
│       │           Threshold Breached        │              │
│       │                  │                  │              │
│       │                  ▼                  │              │
│       │        ┌─────────────────┐          │              │
│       │        │ Orchestrator    │          │              │
│       └────────│ Creates HITL    │──────────┘              │
│                │ Ticket #H-XXXX  │                         │
│                └────────┬────────┘                         │
│                         │                                   │
│                         ▼                                   │
│                ┌─────────────────┐                          │
│                │ Notify Approver │                          │
│                │ (Email/Slack/   │                          │
│                │  Dashboard)     │                          │
│                └────────┬────────┘                          │
│                         │                                   │
│           ┌─────────────┴─────────────┐                     │
│           │                           │                     │
│     ┌─────▼─────┐              ┌──────▼──────┐              │
│     │ Approve   │              │ Reject /    │              │
│     │ (with     │              │ Modify      │              │
│     │ reason)   │              │             │              │
│     └─────┬─────┘              └──────┬──────┘              │
│           │                           │                     │
│           ▼                           ▼                     │
│     ┌──────────┐              ┌──────────────┐             │
│     │ Execute  │              │ Return with  │             │
│     │ Decision │              │ Feedback to  │             │
│     │          │              │ Agent        │             │
│     └──────────┘              └──────────────┘             │
│                                                            │
│  SLA: Critical (pricing, compliance) → <1 hour             │
│       Standard (scheduling, inventory) → <4 hours          │
│       Low (reports, suggestions) → <24 hours               │
└────────────────────────────────────────────────────────────┘
```

---

## 4.4 Phase 3: Full Coordination + Autonomous Execution (Months 6-12)

### Objective
Enterprise-wide rollout with full autonomous execution, circuit breakers, and exception-only human intervention.

### Timeline

| Month | Milestone | Dependencies |
|-------|-----------|-------------|
| 6-7 | Enterprise data connectors: all ERPs, MES, IoT, POS feeds | Enterprise IT cooperation |
| 7-8 | All product lines (full catalog) onboarded | Data quality pass on all lines |
| 8-9 | Circuit breaker framework: soft/hard thresholds per agent | Governance board approval |
| 9-10 | Autonomous mode for Agent-03, Agent-08 (previously L3) activated | >90% accuracy validation |
| 10-11 | Semi-autonomous → Autonomous upgrade for Agents 01, 02, 04 | 3-month HITL intervention <10% |
| 11 | Agent-05 (Market) upgrade to L2 with auto-trading signals | Legal sign-off on automated pricing |
| 12 | Full system Go-Live: legacy systems → monitoring-only mode | Board-level sign-off |

### Scope
- **Full product catalog**: All SKUs across all facilities
- **Autonomy levels**: Agent-03 L3, Agent-08 L3, Agent-09 L3, Agents 01/02/04/07 L2, Agents 05/06 L1
- **Circuit breakers**: All agents have hard limits; Agent-08 can halt any agent for compliance
- **Low-connectivity fallback**: Cached models, conservative safety stock, local queueing
- **Legacy parallel**: Legacy systems in read-only shadow mode; 1-month parallel run before cutover

### Circuits Breaker Architecture

```
┌────────────────────────────────────────────────────────────┐
│                  CIRCUIT BREAKER FRAMEWORK                   │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────┐   │
│  │ Soft Warning │───▶│ Hard Halt   │───▶│ Kill Switch  │   │
│  │              │    │              │    │              │   │
│  │ • KPI breach │    │ • Threshold  │    │ • Manual     │   │
│  │ • Model drift│    │   exceeded   │    │   override   │   │
│  │ • Data qual. │    │ • Compliance │    │ • Full       │   │
│  │   issue      │    │   violation  │    │   shutdown   │   │
│  │              │    │ • Agent      │    │ • Emergency  │   │
│  │ Auto: notify │    │   conflict   │    │   protocol   │   │
│  │ Orchestrator │    │              │    │              │   │
│  │              │    │ Auto: agent  │    │ Auto:        │   │
│  │ Action:      │    │   → advisory │    │   all agents │   │
│  │ continue but │    │   mode       │    │   → advisory │   │
│  │ monitor      │    │              │    │              │   │
│  └─────────────┘    └─────────────┘    └──────────────┘   │
└────────────────────────────────────────────────────────────┘
```

### Additional Team
- +2 × Platform Engineers (K8s, scaling, reliability)
- +1 × Security Engineer (zero-trust, Vault, OPA)
- +1 × Data Engineer (enterprise data quality)
- +1 × Change Manager (enterprise training, rollout coordination)

### ROI Milestones (Cumulative)
- Full enterprise: inventory turnover +15% → est. $5M working capital release
- Margin expansion: 5-8% → est. $15-25M EBITDA improvement ($500M revenue base)
- OEE improvement: >85% → est. $3M in capacity gains
- Manual effort reduction: 40% in procurement, 30% in planning, 50% in reporting
- Forecast accuracy: MAPE <15%, reduced rush shipping costs 25%

---

## 4.5 Migration Strategy

### Dual-Write Pattern

```
┌──────────────┐         ┌────────────────┐         ┌──────────────┐
│              │  Event  │                │  Write   │              │
│   Source     │────────▶│  MAS Agent     │─────────▶│   Delta Lake │
│   System     │         │  (Process)     │          │   (New)      │
│   (ERP/MES)  │         └────────┬───────┘          └──────────────┘
│              │                  │
└──────────────┘                  │ Write (shadow)
                                  ▼
                         ┌────────────────┐
                         │   Legacy DB    │
                         │   (ERP/MES)    │
                         └────────────────┘
```

### Reconciliation Job

```sql
-- Daily reconciliation query example
SELECT 
  source_system,
  record_type,
  COUNT(*) as total_records,
  SUM(CASE WHEN mas_value = legacy_value THEN 1 ELSE 0 END) as matched,
  SUM(CASE WHEN mas_value != legacy_value THEN 1 ELSE 0 END) as mismatched,
  ROUND(AVG(ABS(mas_value - legacy_value) / NULLIF(legacy_value, 0)) * 100, 2) as avg_pct_variance
FROM reconciliation.phase2_daily
WHERE reconciliation_date = CURRENT_DATE
GROUP BY source_system, record_type;
```

### Cutover Criteria (for each phase gate)

| Criterion | Phase 1 | Phase 2 | Phase 3 |
|-----------|---------|---------|---------|
| Data quality pass rate | >90% | >95% | >99% |
| Forecast accuracy (MAPE) | <18% | <15% | <12% |
| Dual-write match rate | >95% | >99% | >99.9% |
| Human intervention rate | N/A (advisory) | <20% | <10% |
| Critical path latency | <5s | <2s | <1s |
| False positive alerts | N/A | <5/day | <2/day |

### Rollback Protocol

1. **Automated detection**: Orchestrator detects KPI breach → circuit breaker → agents → advisory mode
2. **Rollback trigger**: If breach persists >15 minutes → automated rollback to last stable version
3. **Rollback scope**: Model version (MLflow), agent binary (K8s rolling update), or data pipeline (Delta time travel)
4. **Recovery time objective (RTO)**: <2 hours mean-time-to-recover
5. **Recovery point objective (RPO)**: <5 minutes data loss (Kafka retention)

---

## 4.6 ROI Summary by Phase

| Phase | Investment (est.) | Annualized Benefit | ROI Payback |
|-------|------------------|-------------------|-------------|
| Phase 1 (0-3mo) | $500K – $800K | $800K (inventory + data quality) | 6-12 months |
| Phase 2 (3-6mo) | $1.2M – $2.0M | $3M – $5M (inventory + OEE + margin) | 4-6 months |
| Phase 3 (6-12mo) | $2.0M – $3.5M | $15M – $25M (full enterprise) | 2-3 months |
| **Total** | **$3.7M – $6.3M** | **$18.8M – $30.8M** | **3-4 months blended** |

*Note: Benefits assume $500M manufacturing revenue base. Scale proportionally.*

---

*See also: [Risk Register](./05-risk-register.md) | [Evaluation Framework](./07-evaluation-framework.md)*
