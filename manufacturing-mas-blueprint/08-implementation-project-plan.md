# 8. Implementation Project Plan — Gantt Chart & Jira Epic/Story Breakdown

> **12-month program**: 3 phases, 6 epics, 26+ stories, 24 two-week sprints, ~1,130 story points

---

## 8.1 Program Structure Overview

```
┌────────────────────────────────────────────────────────────────────┐
│               MANUFACTURING MAS — PROGRAM PLAN                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  PHASE 1: Visibility Layer + Forecasting Pilot                     │
│  ──────────────────────────────────────────────────────────        │
│  Epic 1.1: Data Foundation & Infrastructure  [SP: 125]            │
│  Epic 1.2: Forecasting Agents (Pilot)       [SP: 105]            │
│  └── Phase 1 Gate ──→ Go/No-Go at Week 12                        │
│                                                                    │
│  PHASE 2: Semi-Autonomous Optimization + HITL                      │
│  ──────────────────────────────────────────────────────────        │
│  Epic 2.1: Execution Agents + HITL Gates  [SP: 228]               │
│  Epic 2.2: Financial & Compliance Engine   [SP: 144]              │
│  └── Phase 2 Gate ──→ Go/No-Go at Week 28                        │
│                                                                    │
│  PHASE 3: Full Autonomous Enterprise Rollout                       │
│  ──────────────────────────────────────────────────────────        │
│  Epic 3.1: Enterprise Expansion + Circuit Breakers [SP: 283]      │
│  Epic 3.2: Optimization, Security & Cutover       [SP: 243]       │
│  └── Phase 3 Gate ──→ Production Go-Live at Week 52              │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 8.2 Gantt Chart

### Gantt — Phase 1: Visibility & Forecast Pilot (Weeks 1-12)

```mermaid
gantt
    title Phase 1 — Visibility Layer + Forecasting Pilot
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    
    section Epic 1.1: Data Foundation
    Sprint 1: Team Formation & Kick-off        :s1p1, 2026-06-01, 2026-06-12
    Kafka Cluster Provisioning                 :done, s1p1, 10d
    Delta Lake (Bronze/Silver/Gold) Setup      :done, s1p1, 10d
    PostgreSQL + MinIO Deployment              :done, s1p1, 8d
    Redis Cache Cluster                        :done, s1p1, 5d
    DQ Gates (Great Expectations × 47 checks)  :crit, s1p1, 10d
    
    Sprint 2: ERP/MES Connectors               :s1p2, 2026-06-15, 2026-06-26
    ERP Connector (SAP/Oracle, 1 product line) :crit, s1p2, 10d
    MES Connector (Basic read)                 :s1p2, 8d
    POS/Retailer Feed Connector                :s1p2, 5d
    Dual-Write Reconciliation Job v1          :s1p2, 8d
    Data Lineage (OpenLineage)                 :s1p2, 5d
    
    Sprint 3: Agent Scaffolding & Monitoring   :s1p3, 2026-06-29, 2026-07-10
    Agent-09 Orchestrator (Health Dashboard)   :crit, s1p3, 10d
    Agent-05 Market Intelligence (Basic)       :s1p3, 8d
    Kafka Topic Structure + CloudEvents Setup  :s1p3, 5d
    Prometheus/Grafana Monitoring Stack        :s1p3, 5d
    
    section Epic 1.2: Forecasting Pilot
    Sprint 3 (con't): Forecasting Models        :s1p3, 2026-06-29, 2026-07-10
    Agent-06 Predictive Analytics (Pilot)       :crit, s1p3, 10d
    Baseline MAPE Measurement                   :s1p3, 5d
    
    Sprint 4: Financial Read-Only + Dashboard  :s1p4, 2026-07-13, 2026-07-24
    Agent-07 Financial (BOM Costing, Read-Only):crit, s1p4, 10d
    Agent-05 Dashboard (Grafana)               :s1p4, 5d
    Agent-06 Forecast Accuracy Tracking        :s1p4, 5d
    Dual-Write Reconciliation Job v2           :s1p4, 5d
    
    Sprint 5: Phase 1 Validation               :s1p5, 2026-07-27, 2026-08-07
    Data Quality Pass Rate Validation (>90%)   :crit, s1p5, 5d
    Forecast MAPE Validation (<18%, 4 weeks)   :crit, s1p5, 5d
    Dual-Write Match Rate Validation (>95%)   :crit, s1p5, 5d
    Security Baseline Audit                    :s1p5, 5d
    Phase 1 Retrospective & Go/No-Go Prep      :milestone, s1p5, 1d
    
    Sprint 6: Buffer + Phase 1 Gate            :s1p6, 2026-08-10, 2026-08-21
    Remediation of Phase 1 Issues              :s1p6, 10d
    Phase 1 Go/No-Go Review w/ CPO, COO, CTO  :milestone, 2026-08-18, 1d
```

### Gantt — Phase 2: Semi-Autonomous + HITL (Weeks 13-28)

```mermaid
gantt
    title Phase 2 — Semi-Autonomous Optimization + HITL Gates
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    
    section Epic 2.1: Execution Agents
    Sprint 7: Agent-01 Procurement (Scaffold)  :s2p1, 2026-08-24, 2026-09-04
    Vendor Scoring Engine (15 Metrics)         :crit, s2p1, 10d
    Kafka Consumer/Producer for Agent-01       :s2p1, 5d
    Price Monitoring + Volatility Detection    :s2p1, 5d
    PO Optimization (EOQ Decider)               :s2p1, 5d
    HITL Integration (Price >5%, PO >$500K)    :s2p1, 5d
    
    Sprint 8: Agent-03 Inventory (Scaffold)    :s2p2, 2026-09-07, 2026-09-18
    Dynamic Reorder Point Engine               :crit, s2p2, 10d
    Safety Stock Optimization                   :s2p2, 8d
    FIFO/FEFO Stock Rotation Logic             :s2p2, 5d
    Dead-Stock Detection (>90d no movement)    :s2p2, 3d
    Cross-Docking Coordination                 :s2p2, 5d
    WMS Integration Connector                  :s2p2, 8d
    
    Sprint 9: Agent-04 Sales & Distribution    :s2p3, 2026-09-21, 2026-10-02
    Order Routing Engine                        :crit, s2p3, 10d
    Fulfillment Prioritization                 :s2p3, 5d
    Channel Pricing Rules Engine               :s2p3, 5d
    Logistics Optimization (TMS Integration)   :s2p3, 8d
    Returns Management Module                  :s2p3, 5d
    
    Sprint 10: Agent-02 Production & MES       :s2p4, 2026-10-05, 2026-10-16
    Machine Scheduling Engine                   :crit, s2p4, 10d
    OEE Tracking (Availability/Performance/Q)  :s2p4, 5d
    Predictive Maintenance Triggers             :s2p4, 8d
    Quality Control (SPC Violation Detection)  :s2p4, 5d
    Bottleneck Resolution Logic                :s2p4, 5d
    MES API Integration (Read/Write)           :s2p4, 8d
    
    Sprint 11: HITL Gate Implementation       :s2p5, 2026-10-19, 2026-10-30
    HITL Gate Proxy Infrastructure             :crit, s2p5, 10d
    Pricing >5% Approval Workflow              :crit, s2p5, 5d
    Production Schedule Override Workflow      :crit, s2p5, 5d
    Supplier Onboarding Gate                   :s2p5, 5d
    Financial Close Approval Gate              :s2p5, 5d
    Orchestrator HITL Dashboard                :s2p5, 5d
    
    section Epic 2.2: Financial & Compliance
    Sprint 12: Agent-07 Financial (Full)       :s2p6, 2026-11-02, 2026-11-13
    Real-Time BOM Costing Engine               :crit, s2p6, 10d
    COGS → Selling Price → Margin Tracking     :crit, s2p6, 8d
    Labor & Overhead Allocation                 :s2p6, 5d
    Cash Flow Projection Model                 :s2p6, 5d
    P&L + Budget vs Actuals                    :s2p6, 5d
    Deterministic Ledger Rules Engine          :crit, s2p6, 8d
    
    Sprint 13: Agent-08 Compliance & Risk      :s2p7, 2026-11-16, 2026-11-27
    SOX Control Automation (47 controls)       :crit, s2p7, 10d
    Regulatory Tracking (GDPR, ISO, ESG)        :s2p7, 8d
    Audit Trail Immutable Logging (WORM)       :s2p7, 5d
    Supply Disruption Early Warning            :s2p7, 5d
    Fallback Protocol Automation               :s2p7, 5d
    
    Sprint 14: Cross-Agent Integration + Gate  :s2p8, 2026-11-30, 2026-12-11
    Agent-06 Forecast → All Agents Pipeline    :crit, s2p8, 10d
    Cross-Agent Conflict Resolution Testing     :s2p8, 5d
    Human Intervention Rate Measurement        :s2p8, 3d
    Phase 2 Go/No-Go Review w/ CFO, COO, CTO  :milestone, 2026-12-08, 1d
```

### Gantt — Phase 3: Enterprise Autonomous Rollout (Weeks 29-52)

```mermaid
gantt
    title Phase 3 — Full Autonomous Enterprise Rollout
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d
    
    section Epic 3.1: Enterprise Expansion
    Sprint 15: Enterprise Data Connectors      :s3p1, 2026-12-14, 2027-01-01
    All ERP Instances Connector (Full Catalog) :crit, s3p1, 15d
    All MES Systems Connector                  :crit, s3p1, 12d
    IoT Sensor Integration Pipeline            :s3p1, 10d
    All POS/Retailer Feeds Integration         :s3p1, 8d
    Enterprise Data Quality Gates (>99%)       :crit, s3p1, 10d
    
    Sprint 16: Multi-Product Line Onboarding   :s3p2, 2027-01-04, 2027-01-22
    SKU Catalog Expansion (All Products)       :crit, s3p2, 15d
    Per-Product-Line Forecast Model Tuning     :crit, s3p2, 10d
    Per-Line OEE Baseline Calibration          :s3p2, 8d
    Per-Line Inventory Parameter Configuration :s3p2, 8d
    Dual-Write Reconciliation v3 (Enterprise)  :s3p2, 10d
    
    Sprint 17: Circuit Breaker Framework       :s3p3, 2027-01-25, 2027-02-12
    Soft Threshold Implementation (Warning)    :crit, s3p3, 10d
    Hard Threshold Implementation (Halt)       :crit, s3p3, 10d
    Kill Switch Framework (Orchestrator)        :crit, s3p3, 8d
    Automated Rollback Pipeline                :s3p3, 8d
    Chaos Engineering Test Suite               :s3p3, 10d
    
    Sprint 18: L3 Autonomous Activation        :s3p4, 2027-02-15, 2027-03-05
    Agent-03 Inventory L3 Activation           :crit, s3p4, 10d
    Agent-08 Compliance L3 Activation          :crit, s3p4, 8d
    Agent-09 Orchestrator L3 Activation        :crit, s3p4, 8d
    L3 Validation Suite (7-day observation)    :s3p4, 10d
    
    Sprint 19: L2 → L3 Upgrade Path           :s3p5, 2027-03-08, 2027-03-26
    Agent-01 Procurement L2→L3 (w/ HITL)      :crit, s3p5, 12d
    Agent-02 Production L2→L3 (w/ HITL)       :crit, s3p5, 12d
    Agent-04 Sales L2→L3 (w/ HITL)            :crit, s3p5, 12d
    Agent-07 Financial L2→L3 (Deterministic)  :s3p5, 8d
    
    section Epic 3.2: Optimization & Security
    Sprint 20: Agent-05 Market Upgrade         :s3p6, 2027-03-29, 2027-04-16
    Auto-Trading Signals (L2 Activation)       :crit, s3p6, 12d
    Competitor Pricing Automation              :s3p6, 8d
    Social/Web Sentiment Pipeline              :s3p6, 8d
    Legal Sign-off for Automated Pricing       :crit, s3p6, 10d
    
    Sprint 21: Security Hardening              :s3p7, 2027-04-19, 2027-05-07
    Zero-Trust (mTLS, OPA, Vault) Full Deploy  :crit, s3p7, 12d
    RBAC/ABAC Implementation                   :s3p7, 8d
    Secrets Management (Vault Auto-Rotation)   :s3p7, 8d
    Penetration Testing (Full Suite)            :s3p7, 10d
    
    Sprint 22: Low-Connectivity Fallback       :s3p8, 2027-05-10, 2027-05-28
    Cached Model Distribution                  :crit, s3p8, 10d
    Conservative Safety Stock Fallback Rules   :s3p8, 5d
    Local Queueing & Replay Mechanism          :s3p8, 8d
    Offline Mode Validation                    :s3p8, 5d
    
    Sprint 23: Parallel Run & Validation       :s3p9, 2027-05-31, 2027-06-18
    Legacy Systems → Read-Only Shadow Mode     :crit, s3p9, 12d
    4-Week Parallel Run (MAS vs Legacy)        :crit, s3p9, 20d
    KPI Validation (All Success Criteria)      :crit, s3p9, 15d
    Enterprise Training Program                :s3p9, 10d
    
    Sprint 24: Go-Live & Cutover               :s3p10, 2027-06-21, 2027-07-02
    Board-Level Sign-Off Review                :milestone, 2027-06-22, 1d
    Production Cutover (Rolling, by region)    :crit, s3p10, 10d
    War Room (24/7 First Week Support)         :crit, s3p10, 10d
    Hypercare (Weeks 2-4 Post-Go-Live)         :s3p10, 10d
```

---

## 8.3 Jira Epic & Story Breakdown

### Epic 1.1: Data Foundation & Infrastructure (125 SP)

| Story ID | Story Name | Story Points | Priority | Dependencies | Assignment |
|----------|-----------|:------------:|:--------:|-------------|------------|
| **MAS-001** | **Provision Kafka Cluster (5 topics, 3 brokers)** | 13 | P0-Critical | — | Data Engineer |
| **MAS-002** | **Deploy Delta Lake (Bronze/Silver/Gold architecture)** | 13 | P0-Critical | — | Data Engineer |
| **MAS-003** | **Deploy PostgreSQL + MinIO object store** | 8 | P0-Critical | — | DevOps |
| **MAS-004** | **Deploy Redis cache cluster** | 5 | P1-High | — | DevOps |
| **MAS-005** | **Implement data quality gates (Great Expectations × 47)** | 13 | P0-Critical | MAS-001, MAS-002 | Data Engineer |
| **MAS-006** | **Build ERP connector (SAP/Oracle, 1 product line)** | 13 | P0-Critical | MAS-001, MAS-002 | Backend Engineer |
| **MAS-007** | **Build MES connector (read-only, basic)** | 8 | P1-High | MAS-001 | Integration Spec. |
| **MAS-008** | **Build POS/retailer feed connector** | 5 | P1-High | MAS-001 | Data Engineer |
| **MAS-009** | **Implement dual-write reconciliation job v1** | 8 | P0-Critical | MAS-006, MAS-007 | Backend Engineer |
| **MAS-010** | **Set up OpenLineage data lineage tracking** | 5 | P1-High | MAS-002 | Data Engineer |
| **MAS-011** | **Provision Agent-09 Orchestrator scaffold + health dashboard** | 13 | P0-Critical | MAS-001, MAS-002 | Backend Engineer |
| **MAS-012** | **Deploy Prometheus/Grafana monitoring stack** | 8 | P1-High | MAS-001 | DevOps |
| **MAS-013** | **Define Kafka topic structure + CloudEvents schemas** | 8 | P0-Critical | MAS-001 | Backend Engineer |
| **MAS-014** | **Set up CI/CD pipeline (GitHub Actions + ArgoCD)** | 5 | P1-High | — | DevOps |
| **Total** | | **125** | | | |

#### Story Details — Epic 1.1 Key Stories

**MAS-001: Provision Kafka Cluster**

| Field | Value |
|-------|-------|
| **Description** | Deploy a 3-broker Kafka cluster with the following 5 topics: `mas.events.procurement`, `mas.events.production`, `mas.events.inventory`, `mas.events.sales`, `mas.events.market`. Configure 3 partitions per topic, replication factor 3, retention 90 days. Integrate with Confluent Schema Registry. |
| **Acceptance Criteria** | ① All 5 topics exist with correct partition/replication config ② Producer/consumer connectivity verified ③ Schema Registry functional ④ Dead-letter queue configured ⑤ Throughput baseline established (50K msg/min) ⑥ 3-node cluster shows healthy in broker metrics |
| **Technical Notes** | Use Strimzi Operator on K8s or Confluent Operator. Configure TLS encryption, SASL/SCRAM auth. Set `min.insync.replicas=2`. |
| **Definition of Done** | Kafka cluster operational, topics created, schema registry running, health dashboard showing broker status |

**MAS-005: Data Quality Gates (Great Expectations × 47)**

| Field | Value |
|-------|-------|
| **Description** | Implement 47 automated data quality checks across all data sources using Great Expectations. Gates include: schema conformance (18), completeness/null checks (10), range/outlier detection (8), referential integrity (6), freshness/timeliness (5). |
| **Acceptance Criteria** | ① All 47 checks defined and deployed ② Data quality dashboard showing pass/fail per gate ③ Alert on >5% failures ④ Gate before agent consumption enforced ⑤ >90% data quality pass rate validated |
| **Technical Notes** | Implement as pre-consumption filter in Kafka Streams. Failed records → quarantine topic with reason code. |
| **Definition of Done** | All 47 gates operational, dashboard showing real-time pass rates, alerting configured |

---

### Epic 1.2: Forecasting Agents — Pilot (105 SP)

| Story ID | Story Name | Story Points | Priority | Dependencies | Assignment |
|----------|-----------|:------------:|:--------:|-------------|------------|
| **MAS-015** | **Agent-05: Market Intelligence (Basic — competitor pricing + sentiment)** | 13 | P0-Critical | MAS-001, MAS-013 | ML Engineer |
| **MAS-016** | **Agent-06: Predictive Analytics — Baseline forecast model (Prophet)** | 13 | P0-Critical | MAS-002, MAS-006, MAS-008 | ML Engineer |
| **MAS-017** | **Agent-06: Forecast evaluation dashboard (MAPE/WAPE tracking)** | 8 | P0-Critical | MAS-016 | ML Engineer |
| **MAS-018** | **Agent-07: Financial — BOM costing engine (rule-based, read-only)** | 13 | P0-Critical | MAS-002, MAS-006 | Backend Engineer |
| **MAS-019** | **Agent-07: Basic margin tracking dashboard** | 8 | P1-High | MAS-018 | Backend Engineer |
| **MAS-020** | **Agent-05: Market dashboard (Grafana)** | 5 | P1-High | MAS-015 | Full-Stack |
| **MAS-021** | **Agent-09: System health dashboard (Phase 1 view)** | 13 | P0-Critical | MAS-011 | Full-Stack |
| **MAS-022** | **Agent-06: Forecast → Agent-07 forecast consumption pipeline** | 5 | P1-High | MAS-016, MAS-018 | Backend Engineer |
| **MAS-023** | **Forecast baseline measurement (4 weeks of data)** | 8 | P0-Critical | MAS-016 | ML Engineer |
| **MAS-024** | **Phase 1 validation: MAPE <18%, DQ >90%, dual-write >95%** | 13 | P0-Critical | All above | Program Manager |
| **MAS-025** | **Phase 1 Go/No-Go gate review documentation + sign-off** | 3 | P0-Critical | MAS-024 | Program Manager |
| **MAS-026** | **Security baseline: mTLS, Vault deployment, RBAC init** | 3 | P1-High | MAS-003 | Security Engineer |
| **Total** | | **105** | | | |

#### Story Details — Epic 1.2 Key Stories

**MAS-016: Agent-06 Baseline Forecast Model (Prophet)**

| Field | Value |
|-------|-------|
| **Description** | Implement Prophet-based demand forecasting for 1 pilot product line (≤50 SKUs). Inputs: 3+ years historical sales data, seasonality, trend. Outputs: 1-month forecast with confidence intervals (80%, 95%). Store results in Delta Lake Gold layer. |
| **Acceptance Criteria** | ① Forecast MAPE <18% on 4-week holdout ② 80% and 95% confidence intervals generated ③ Forecast published to `mas.events.forecast` topic ④ Model versioned in MLflow ⑤ Retraining pipeline stub implemented ⑥ Forecast latency <5s per SKU |
| **Technical Notes** | Use Prophet with additive seasonality. Hyperparameter tuning via Optuna (50 iterations). Validate against simple moving average baseline. |
| **Definition of Done** | Forecast pipeline running, MAPE tracked, model in MLflow, validated against baseline |

**MAS-018: Agent-07 BOM Costing Engine**

| Field | Value |
|-------|-------|
| **Description** | Implement deterministic, rule-based Bill-of-Materials costing engine. Pulls raw material prices (from ERP + Agent-01 price data), labor rates from HR system, overhead allocation rates. Calculates standard cost, current cost, and variance. Read-only in Phase 1. |
| **Acceptance Criteria** | ① BOM cost calculated for all SKUs in pilot line ② Cost breakdown: raw materials, labor, overhead, logistics ③ Variance tracking (standard vs actual) ④ All outputs auditable with data lineage ⑤ No AI/ML used — purely rule-based ⑥ API endpoint for cost queries |
| **Technical Notes** | Implement as Python module with PostgreSQL persistence. Cost roll-up: BOM level × quantity × (material + labor + overhead). |
| **Definition of Done** | Cost engine operational, variance tracked, lineage documented, read-only API available |

---

### Epic 2.1: Execution Agents + HITL Gates (228 SP)

| Story ID | Story Name | Story Points | Priority | Dependencies | Assignment |
|----------|-----------|:------------:|:--------:|-------------|------------|
| **MAS-027** | **Agent-01: Procurement — Vendor scoring engine (15 metrics)** | 13 | P0-Critical | MAS-001, MAS-013 | Backend Engineer |
| **MAS-028** | **Agent-01: Price monitoring + volatility detection** | 8 | P0-Critical | MAS-015 (market data) | ML Engineer |
| **MAS-029** | **Agent-01: PO optimization (EOQ decider)** | 8 | P1-High | MAS-027 | Backend Engineer |
| **MAS-030** | **Agent-01: HITL integration (price >5%, PO >$500K)** | 8 | P0-Critical | MAS-027, MAS-028 | Backend Engineer |
| **MAS-031** | **Agent-01: Alternative sourcing analysis** | 5 | P1-High | MAS-027 | ML Engineer |
| **MAS-032** | **Agent-01: ESG compliance scoring integration** | 5 | P2-Medium | MAS-027 | Backend Engineer |
| **MAS-033** | **Agent-03: Dynamic reorder point engine** | 13 | P0-Critical | MAS-001, MAS-016 (forecast) | Backend Engineer |
| **MAS-034** | **Agent-03: Safety stock optimization** | 8 | P0-Critical | MAS-033 | Backend Engineer |
| **MAS-035** | **Agent-03: FIFO/FEFO stock rotation logic** | 5 | P1-High | MAS-033 | Backend Engineer |
| **MAS-036** | **Agent-03: Dead-stock detection (>90d no movement)** | 3 | P1-High | MAS-033 | Backend Engineer |
| **MAS-037** | **Agent-03: Cross-docking coordination** | 5 | P2-Medium | MAS-033 | Backend Engineer |
| **MAS-038** | **Agent-03: WMS integration connector** | 8 | P0-Critical | MAS-001 | Integration Spec. |
| **MAS-039** | **Agent-04: Order routing engine** | 13 | P0-Critical | MAS-001, MAS-016 | Backend Engineer |
| **MAS-040** | **Agent-04: Fulfillment prioritization** | 8 | P1-High | MAS-039 | Backend Engineer |
| **MAS-041** | **Agent-04: Channel pricing rules engine** | 8 | P1-High | MAS-039 | Backend Engineer |
| **MAS-042** | **Agent-04: Logistics optimization (TMS integration)** | 8 | P0-Critical | MAS-001 | Integration Spec. |
| **MAS-043** | **Agent-04: Returns management module** | 5 | P2-Medium | MAS-039 | Backend Engineer |
| **MAS-044** | **Agent-02: Machine scheduling engine** | 13 | P0-Critical | MAS-001, MAS-016 | Backend Engineer |
| **MAS-045** | **Agent-02: OEE tracking (availability/performance/quality)** | 8 | P0-Critical | MAS-044 | Backend Engineer |
| **MAS-046** | **Agent-02: Predictive maintenance triggers (XGBoost)** | 13 | P0-Critical | MAS-044 | ML Engineer |
| **MAS-047** | **Agent-02: Quality control (SPC violation detection)** | 8 | P1-High | MAS-044 | Backend Engineer |
| **MAS-048** | **Agent-02: Bottleneck resolution logic** | 5 | P1-High | MAS-044 | Backend Engineer |
| **MAS-049** | **Agent-02: MES API integration (read/write)** | 8 | P1-High | MAS-001 | Integration Spec. |
| **MAS-116** | **Agent-02: Rapid retraining trigger (OEE >10% drop or defects >3σ)** | 5 | P1-High | MAS-044, MAS-045, MAS-046 | ML Engineer |
| **MAS-050** | **HITL gate proxy infrastructure (Orchestrator component)** | 13 | P0-Critical | Agent-09 | Backend Engineer |
| **MAS-051** | **Pricing >5% HITL approval workflow** | 5 | P0-Critical | MAS-050 | Backend Engineer |
| **MAS-052** | **Production schedule override HITL workflow** | 5 | P0-Critical | MAS-050 | Backend Engineer |
| **MAS-053** | **Supplier onboarding HITL gate** | 3 | P1-High | MAS-050 | Backend Engineer |
| **MAS-054** | **Financial close HITL approval gate** | 3 | P0-Critical | MAS-050 | Backend Engineer |
| **MAS-055** | **Orchestrator HITL dashboard (Phase 2)** | 8 | P0-Critical | MAS-050 | Full-Stack |
| **Total** | | **228** | | | |

#### Story Details — Epic 2.1 Key Stories

**MAS-027: Agent-01 Vendor Scoring Engine (15 Metrics)**

| Field | Value |
|-------|-------|
| **Description** | Implement a composite vendor scoring engine with 15 weighted metrics across 5 categories: Quality (OTIF, defect rate, ppm), Cost (price competitiveness, payment terms), Delivery (lead time reliability, fill rate), ESG (EcoVadis/Sustainalytics score, carbon footprint, labor compliance), Relationship (contract compliance, communication, innovation). Weight profiles per commodity type (critical, leverage, bottleneck, routine). |
| **Acceptance Criteria** | ① 15 metrics computed per vendor per quarter ② Weight profiles for ≥4 commodity types ③ Composite score (0-100) with category breakdown ④ Score published to Delta Lake + `mas.events.procurement` ⑤ Escalation if score <60/100 ⑥ Confidence interval per score | ⑦ All metrics traceable to source data |
| **Technical Notes** | Pure NumPy — no ML for scoring. Trend detection (3-quarter moving average) highlights improving/declining vendors. |
| **Definition of Done** | Scoring engine operational, scorecards generated, trend detection active, HITL triggers integrated |

**MAS-044: Agent-02 Machine Scheduling Engine**

| Field | Value |
|-------|-------|
| **Description** | Implement a constraint-based production scheduling engine. Inputs: production orders (ERP), machine availability (MES), material availability (Agent-03), shift calendar. Optimizes for: due date adherence > on-time starts > machine utilization. Outputs: sequenced schedule with machine assignments, estimated cycle times. |
| **Acceptance Criteria** | ① Schedule generated for 3 product lines ② Constraint satisfaction: machine capacity, material availability, shift calendar ③ Objective function: due date adherence (weight 0.5), OEE impact (0.3), changeover minimization (0.2) ④ Schedule regeneration within 5 minutes ⑤ >95% schedule adherence vs manual baseline |
| **Technical Notes** | Use Google OR-Tools CP-SAT solver for constraint optimization. Fallback: FIFO-based heuristic if solver times out (>5 min). |
| **Definition of Done** | Schedule engine operational, validated against manual schedule, integrated with MES read/write |

**MAS-050: HITL Gate Proxy Infrastructure**

| Field | Value |
|-------|-------|
| **Description** | Implement the centralized HITL gate proxy as an Orchestrator (Agent-09) component. Receives agent decisions, evaluates against threshold config, routes to approval via Slack/Email/Dashboard, tracks SLA, escalates on timeout. Every decision logged with: input snapshot, model version, confidence, alternatives, business impact, approver, outcome. |
| **Acceptance Criteria** | ① HITL ticket lifecycle: created → pending → approved/rejected → executed ② SLA enforcement: P1 (<1h), P2 (<4h), P3 (<24h) ③ Auto-escalation on SLA breach ④ Notification via Slack + Email + Dashboard ⑤ Audit log with full provenance ⑥ Support for approve/reject/modify ⑦ >100 concurrent ticket capacity |
| **Technical Notes** | Stateful service backed by PostgreSQL. Ticket schema: `{id, agent_source, decision_type, threshold_config, actual_value, proposer, approver, status, sla_deadline, escalation_level, created_at, resolved_at, input_snapshot, alternatives, confidence, business_impact}` |
| **Definition of Done** | HITL proxy operational, tickets flowing, SLA enforced, dashboard showing pending/breached tickets |

---

### Epic 2.2: Financial & Compliance Engine (144 SP)

| Story ID | Story Name | Story Points | Priority | Dependencies | Assignment |
|----------|-----------|:------------:|:--------:|-------------|------------|
| **MAS-056** | **Agent-07: Real-time BOM costing engine (Phase 2 upgrade)** | 13 | P0-Critical | MAS-018 | Backend Engineer |
| **MAS-057** | **Agent-07: COGS → selling price → gross/net margin tracking** | 8 | P0-Critical | MAS-056 | Backend Engineer |
| **MAS-058** | **Agent-07: Labor & overhead allocation engine** | 8 | P1-High | MAS-056 | Backend Engineer |
| **MAS-059** | **Agent-07: Cash flow projection model** | 8 | P1-High | MAS-056 | Backend Engineer |
| **MAS-060** | **Agent-07: P&L + Budget vs Actuals** | 8 | P0-Critical | MAS-057 | Backend Engineer |
| **MAS-061** | **Agent-07: Deterministic ledger rules engine** | 13 | P0-Critical | MAS-056, MAS-057 | Backend Engineer |
| **MAS-062** | **Agent-07: CFO dashboard (margin, cash flow, COGS variance)** | 8 | P1-High | MAS-060 | Full-Stack |
| **MAS-063** | **Agent-08: SOX control automation (47 controls)** | 13 | P0-Critical | MAS-050, MAS-061 | Compliance Eng. |
| **MAS-064** | **Agent-08: Regulatory tracking (GDPR, ISO 9001/27001, ESG)** | 8 | P0-Critical | MAS-063 | Compliance Eng. |
| **MAS-065** | **Agent-08: Immutable audit trail (WORM storage)** | 8 | P0-Critical | MAS-001 (MinIO) | Backend Engineer |
| **MAS-066** | **Agent-08: Supply disruption early warning** | 8 | P1-High | MAS-015, MAS-016 | ML Engineer |
| **MAS-067** | **Agent-08: Fallback protocol automation** | 5 | P1-High | MAS-063 | Backend Engineer |
| **MAS-068** | **Agent-08: Cyber-risk monitoring integration** | 5 | P2-Medium | MAS-063 | Security Engineer |
| **MAS-069** | **Cross-agent integration: Agent-06 → all agents forecast consumption** | 13 | P0-Critical | MAS-016 | Backend Engineer |
| **MAS-070** | **Conflict resolution testing (8 rules from governance matrix)** | 5 | P1-High | MAS-069 | Program Manager |
| **MAS-117** | **Cross-agent conflict resolution rules (8 rules from governance docs)** | 5 | P1-High | MAS-069 | Backend Engineer |
| **MAS-071** | **Phase 2 validation: intervention <20%, turnover +5%, margin +1%** | 8 | P0-Critical | All Epic 2.x | Program Manager |
| **Total** | | **144** | | | |

#### Story Details — Epic 2.2 Key Stories

**MAS-061: Deterministic Ledger Rules Engine**

| Field | Value |
|-------|-------|
| **Description** | Implement the deterministic, auditable financial rules engine that enforces: double-entry accounting (every debit has matching credit), segregation of duties (no single agent creates + approves), cost allocation rules, revenue recognition rules, inter-company elimination rules. NO AI/ML in this engine — pure rule-based. Every journal entry has complete audit lineage. |
| **Acceptance Criteria** | ① Double-entry enforcement: all transactions balance ② Segregation of duties enforced: create ≠ approve ③ Cost allocation: by activity-based costing rules ④ Revenue recognition: per ASC 606 rules ⑤ Every entry has: source, reason, approver, timestamp ⑥ No AI/ML used — rule-based only ⑦ SOX control integration (47 controls) |
| **Technical Notes** | Implement as deterministic Python module. Input from all agents. Output: general ledger entries → PostgreSQL → WORM audit log. |
| **Definition of Done** | Ledger engine operational, SOX controls integrated, audit lineage complete, certified by compliance |

**MAS-063: SOX Control Automation (47 Controls)**

| Field | Value |
|-------|-------|
| **Description** | Implement automated SOX controls across all agents. 47 controls organized by: Access Control (8), Change Management (6), Segregation of Duties (5), Data Integrity (10), Financial Reporting (8), IT Operations (6), Vendor Management (4). Each control has: ID, description, frequency (real-time/daily/weekly), test procedure, pass/fail criteria, evidence capture. |
| **Acceptance Criteria** | ① All 47 controls defined and deployed ② Real-time monitoring for continuous controls ③ Automated evidence collection for audit ④ Dashboard showing control pass/fail rate ⑤ >98% control pass rate ⑥ SOX audit readiness confirmed by external auditor |
| **Technical Notes** | Use OPA (Open Policy Agent) for policy-as-code controls. Evidence stored in WORM MinIO. |
| **Definition of Done** | All controls operational, evidence pipeline running, dashboards live, auditor-confirmed readiness |

**MAS-069: Cross-Agent Forecast Integration**

| Field | Value |
|-------|-------|
| **Description** | Implement the pipeline that distributes Agent-06 forecasts to all consuming agents. Agent-01 (procurement demand), Agent-02 (production scheduling), Agent-03 (inventory reorder), Agent-04 (fulfillment planning), Agent-07 (financial projections). Includes: forecast topic subscription, schema validation, confidence-aware consumption (agents use lower-confidence bounds conservatively), drift monitoring. |
| **Acceptance Criteria** | ① Forecast published to `mas.events.forecast` topic ② All 5 consuming agents receive and process forecast ③ Confidence-aware consumption implemented ④ Forecast → reorder → schedule → fulfillment pipeline validated end-to-end ⑤ Latency: forecast publish → agent consumption <500ms ⑥ Drift monitoring: weekly MAPE per agent |
| **Technical Notes** | Use Kafka consumer groups per agent. Schema Registry enforces compatibility. Dead-letter queue for failed consumption. |
| **Definition of Done** | End-to-end forecast pipeline operational, all consuming agents integrated, drift monitoring live |

---

### Epic 3.1: Enterprise Expansion + Circuit Breakers (283 SP)

| Story ID | Story Name | Story Points | Priority | Dependencies | Assignment |
|----------|-----------|:------------:|:--------:|-------------|------------|
| **MAS-072** | **Enterprise ERP connector (all instances, full catalog)** | 21 | P0-Critical | MAS-006 | Data Engineer |
| **MAS-073** | **Enterprise MES connector (all plants)** | 13 | P0-Critical | MAS-007 | Integration Spec. |
| **MAS-074** | **IoT sensor data pipeline (all production lines)** | 13 | P0-Critical | MAS-002 | Data Engineer |
| **MAS-075** | **Enterprise POS/retailer feeds (all channels)** | 8 | P1-High | MAS-008 | Data Engineer |
| **MAS-076** | **Enterprise data quality gates (>99% pass rate)** | 21 | P0-Critical | MAS-005 | Data Engineer |
| **MAS-077** | **Full SKU catalog onboarding (all products, all facilities)** | 21 | P0-Critical | MAS-072, MAS-076 | Data Engineer |
| **MAS-078** | **Per-product-line forecast model tuning** | 13 | P1-High | MAS-016, MAS-077 | ML Engineer |
| **MAS-079** | **Per-line OEE baseline calibration** | 8 | P1-High | MAS-073 | Backend Engineer |
| **MAS-080** | **Per-line inventory parameter configuration** | 8 | P1-High | MAS-033, MAS-077 | Backend Engineer |
| **MAS-081** | **Dual-write reconciliation v3 (enterprise)** | 13 | P0-Critical | MAS-009, MAS-077 | Backend Engineer |
| **MAS-082** | **Circuit breaker — soft threshold framework (warning)** | 13 | P0-Critical | MAS-050 | Backend Engineer |
| **MAS-083** | **Circuit breaker — hard threshold framework (halt)** | 13 | P0-Critical | MAS-082 | Backend Engineer |
| **MAS-084** | **Circuit breaker — kill switch framework (Orchestrator)** | 8 | P0-Critical | MAS-083 | Backend Engineer |
| **MAS-085** | **Automated rollback pipeline (MLflow + K8s)** | 8 | P0-Critical | MAS-084 | DevOps |
| **MAS-086** | **Chaos engineering test suite** | 13 | P1-High | MAS-084 | DevOps |
| **MAS-087** | **Agent-03 inventory L3 autonomous activation** | 13 | P0-Critical | MAS-033, MAS-084 | Backend Engineer |
| **MAS-088** | **Agent-08 compliance L3 autonomous activation** | 8 | P0-Critical | MAS-063, MAS-084 | Compliance Eng. |
| **MAS-089** | **Agent-09 orchestrator L3 autonomous activation** | 8 | P0-Critical | MAS-011, MAS-084 | Backend Engineer |
| **MAS-090** | **L3 validation suite (7-day observation window)** | 13 | P0-Critical | MAS-087, MAS-088, MAS-089 | Program Manager |
| **MAS-091** | **Agent-01 procurement L2→L3 upgrade** | 13 | P0-Critical | MAS-030, MAS-090 | Backend Engineer |
| **MAS-092** | **Agent-02 production L2→L3 upgrade** | 13 | P0-Critical | MAS-044, MAS-090 | Backend Engineer |
| **MAS-093** | **Agent-04 sales L2→L3 upgrade** | 13 | P0-Critical | MAS-039, MAS-090 | Backend Engineer |
| **MAS-094** | **Agent-07 financial L2→L3 upgrade** | 8 | P0-Critical | MAS-061, MAS-090 | Backend Engineer |
| **Total** | | **283** | | | |

#### Story Details — Epic 3.1 Key Stories

**MAS-076: Enterprise Data Quality Gates (>99% Pass Rate)**

| Field | Value |
|-------|-------|
| **Description** | Scale Phase 1 DQ gates (47 checks) to enterprise level: expand to cover all data sources (all ERPs, MES, IoT, POS, market feeds), add automated remediation for common failures, implement self-healing pipelines. Target >99% pass rate from >95% Phase 2 baseline. Add: schema drift auto-detection, anomaly-based quality scoring, proactive data profiling. |
| **Acceptance Criteria** | ① DQ gates cover 100% of enterprise data sources ② >99% pass rate sustained for 4 consecutive weeks ③ Auto-remediation for ≥5 common failure types ④ Schema drift detection with auto-notification ⑤ Cross-source referential integrity validated ⑥ DQ score per data source, per agent consumption |
| **Technical Notes** | Use Great Expectations Cloud or Deequ at scale. Failed records routed to quarantine with automated retry. |
| **Definition of Done** | Enterprise DQ coverage, >99% pass rate validated, remediation pipeline operational |

**MAS-082/083/084: Circuit Breaker Framework**

| Field | Value |
|-------|-------|
| **Description** | Implement 3-tier circuit breaker framework across all agents: **Soft (L1 warning)** — KPI breach triggers Orchestrator notification, continues execution but with monitoring flag; **Hard (L2 halt)** — threshold exceeded (e.g., forecast MAPE >25%, price deviation >10%) triggers agent → advisory mode, all decisions require HITL; **Kill switch (L3)** — Orchestrator can emergency-stop any/all agents, transitions entire system to advisory mode. |
| **Acceptance Criteria** | ① Soft threshold triggers per-agent warning with dashboard alert ② Hard threshold triggers agent → advisory mode within 30s ③ Kill switch can halt any agent or all agents ④ Rollback initiated within 2 minutes of kill switch ⑤ Configurable threshold per agent, per KPI ⑥ Audit log: all circuit breaker events with timestamps |
| **Technical Notes** | Circuit breaker state machine: CLOSED (normal) → WARN (soft breach) → OPEN (hard breach/agent halted) → HALF-OPEN (manual reset) → CLOSED. State persisted in Redis with K8s configmap fallback. |
| **Definition of Done** | All 3 tiers operational, tested via chaos engineering, integrated with all agents |

---

### Epic 3.2: Optimization, Security & Cutover (243 SP)

| Story ID | Story Name | Story Points | Priority | Dependencies | Assignment |
|----------|-----------|:------------:|:--------:|-------------|------------|
| **MAS-095** | **Agent-05: Auto-trading signals (L2 activation)** | 13 | P0-Critical | MAS-015 | ML Engineer |
| **MAS-096** | **Agent-05: Competitor pricing automation** | 8 | P1-High | MAS-015 | ML Engineer |
| **MAS-097** | **Agent-05: Social/web sentiment pipeline (full)** | 8 | P1-High | MAS-015 | Data Engineer |
| **MAS-098** | **Agent-05: Legal sign-off for automated pricing** | 5 | P0-Critical | MAS-095 | Legal/Compliance |
| **MAS-099** | **Zero-trust full deployment (mTLS, OPA, Vault)** | 21 | P0-Critical | MAS-011, MAS-012 | Security Engineer |
| **MAS-100** | **RBAC/ABAC implementation (all agents)** | 13 | P0-Critical | MAS-099 | Security Engineer |
| **MAS-101** | **Secrets management (Vault auto-rotation)** | 8 | P0-Critical | MAS-099 | Security Engineer |
| **MAS-102** | **Penetration testing (full suite)** | 13 | P1-High | MAS-099 | Security Engineer |
| **MAS-103** | **Low-connectivity: cached model distribution** | 13 | P0-Critical | MAS-084, MAS-103 | DevOps |
| **MAS-104** | **Low-connectivity: conservative safety stock fallback** | 8 | P0-Critical | MAS-033, MAS-103 | Backend Engineer |
| **MAS-105** | **Low-connectivity: local queueing & replay mechanism** | 8 | P0-Critical | MAS-001, MAS-103 | Backend Engineer |
| **MAS-106** | **Low-connectivity: offline mode validation** | 5 | P1-High | MAS-104, MAS-105 | DevOps |
| **MAS-107** | **Legacy systems → read-only shadow mode transition** | 13 | P0-Critical | MAS-081 | Program Manager |
| **MAS-108** | **4-week parallel run (MAS vs Legacy)** | 21 | P0-Critical | MAS-107 | Program Manager |
| **MAS-109** | **Enterprise KPI validation (all success criteria)** | 13 | P0-Critical | MAS-108 | Program Manager |
| **MAS-110** | **Enterprise training program (all user roles)** | 13 | P0-Critical | MAS-108 | Change Manager |
| **MAS-111** | **Board-level sign-off review preparation** | 8 | P0-Critical | MAS-108, MAS-109 | Program Manager |
| **MAS-112** | **Production cutover (rolling, by region)** | 21 | P0-Critical | MAS-111 | Program Manager |
| **MAS-113** | **War room (24/7 first week support)** | 13 | P0-Critical | MAS-112 | Program Manager |
| **MAS-114** | **Hypercare (weeks 2-4 post-go-live)** | 13 | P0-Critical | MAS-113 | Program Manager |
| **MAS-115** | **Project close-out + lessons learned** | 5 | P2-Medium | MAS-114 | Program Manager |
| **Total** | | **243** | | | |

#### Story Details — Epic 3.2 Key Stories

**MAS-099: Zero-Trust Full Deployment**

| Field | Value |
|-------|-------|
| **Description** | Implement full zero-trust security architecture: **mTLS** for all inter-agent and inter-service communication (no plain HTTP), **OPA/Gatekeeper** for policy-as-code admission control on K8s, **Vault** for secrets management with auto-rotation (every 30 days). Network policies: deny-all by default, allow only specific agent-to-agent flows. Service mesh (Istio/Linkerd) for observability + security. |
| **Acceptance Criteria** | ① All inter-service communication uses mTLS ② OPA policies enforced for all K8s deployments ③ Vault secrets rotated automatically every 30 days ④ Network policies: default-deny with explicit allow rules ⑤ Service mesh sidecars injected in all pods ⑥ No plain-text secrets in any config ⑦ Penetration test passes with zero critical findings |
| **Technical Notes** | Use cert-manager for mTLS certificate management. OPA Gatekeeper for admission webhook. Vault agent injector for secrets. |
| **Definition of Done** | Zero-trust deployed, pen test passed, all services encrypted, secrets auto-rotating |

**MAS-108: 4-Week Parallel Run (MAS vs Legacy)**

| Field | Value |
|-------|-------|
| **Description** | Execute 4-week parallel run where MAS operates in shadow mode alongside legacy systems. Both systems process all transactions independently. Daily reconciliation: compare outputs, identify discrepancies, root-cause analysis. Escalation: any discrepancy >0.1% of transaction value → immediate HITL. Success criteria for cutover: >99.9% dual-write match rate, <5% human intervention, all KPIs within target. |
| **Acceptance Criteria** | ① All transactions processed by both systems for 4 weeks ② Daily reconciliation: match rate >99.9% by week 4 ③ Discrepancy tracking: root cause for every mismatch ④ KPI tracking: both systems' metrics compared ⑤ Human intervention rate <5% by week 4 ⑥ Cutover criteria met: MAPE <12%, inventory turnover +15%, margin +5-8%, fulfillment >98% ⑦ Exec sign-off obtained |
| **Technical Notes** | Dedicated reconciliation jobs run daily. Output: match/mismatch report by transaction type. Mismatches categorized: timing difference, data quality, logic error, agent error. |
| **Definition of Done** | Parallel run completed, cutover criteria met, exec sign-off obtained, transition plan approved |

---

## 8.4 Sprint-by-Sprint Resource Plan

### Core Team (Weeks 1-52)

| Role | Phase 1 (W1-12) | Phase 2 (W13-28) | Phase 3 (W29-52) |
|------|:--------------:|:---------------:|:----------------:|
| **Program Manager / Scrum Master** | 1.0 FTE | 1.0 FTE | 1.0 FTE |
| **Data Engineer** | 1.5 FTE | 1.5 FTE | 2.0 FTE |
| **Backend Engineer** | 1.0 FTE | 2.0 FTE | 3.0 FTE |
| **ML Engineer** | 1.0 FTE | 1.0 FTE | 1.5 FTE |
| **Full-Stack Developer** | 0.5 FTE | 1.0 FTE | 1.0 FTE |
| **DevOps / Platform Engineer** | 1.0 FTE | 1.0 FTE | 2.0 FTE |
| **Security Engineer** | 0.5 FTE | 0.5 FTE | 1.0 FTE |
| **Integration Specialist** | 0.5 FTE | 1.0 FTE | 1.0 FTE |
| **Compliance Engineer** | 0 FTE | 0.5 FTE | 1.0 FTE |
| **Change Manager** | 0 FTE | 0 FTE | 1.0 FTE |
| **Domain Experts (Supply Chain, Finance)** | 0.5 FTE | 0.5 FTE | 0.5 FTE |
| **Total FTE** | **7.5** | **10.0** | **15.0** |

### Sprint Capacity

| Metric | Value |
|--------|-------|
| Sprint length | 2 weeks (10 working days) |
| Avg team velocity (Phase 1) | 50-60 SP/sprint |
| Avg team velocity (Phase 2) | 65-80 SP/sprint |
| Avg team velocity (Phase 3) | 85-105 SP/sprint |
| Target utilization | 80% (20% buffer for unplanned work) |

---

## 8.5 Dependency Map

### Critical Path Dependencies

```
Phase 1                    Phase 2                          Phase 3
────────                    ────────                         ────────

MAS-001 (Kafka) ──→ MAS-006 (ERP Connector) ──→ MAS-027 (Agent-01) ──→ MAS-082 (Circuit Breaker Soft)
     │                        │                       │                      │
     ├─→ MAS-005 (DQ Gates) ──┤                       ├─→ MAS-033 (Agent-03) ─┤
     │                        │                       │                      │
     └─→ MAS-013 (Topics) ────┤                       ├─→ MAS-039 (Agent-04) ─┤
                              │                       │                      │
                              ├─→ MAS-016 (Forecast) ──┤                      ├─→ MAS-083 (Circuit Breaker Hard)
                              │                       │                      │
                              │                       ├─→ MAS-044 (Agent-02) ─┤
                              │                       │                      │
                              │                       └─→ MAS-050 (HITL) ─────┤
                              │                                                │
                              ├─→ MAS-018 (BOM Cost) ──→ MAS-056 (Full Fin) ──┤
                              │                                                │
                              └─→ MAS-015 (Market) ────→ MAS-063 (Compliance) ──┘
                                                                                │
                                                                                └─→ MAS-084 (Kill Switch)
                                                                                    │
                                                                                    ├─→ MAS-087 (Agent-03 L3)
                                                                                    ├─→ MAS-088 (Agent-08 L3)
                                                                                    ├─→ MAS-089 (Agent-09 L3)
                                                                                    ├─→ MAS-091 (Agent-01 L3)
                                                                                    ├─→ MAS-092 (Agent-02 L3)
                                                                                    ├─→ MAS-093 (Agent-04 L3)
                                                                                    └─→ MAS-094 (Agent-07 L3)
                                                                                        │
                                                                                        └─→ MAS-099 (Zero-Trust)
                                                                                            │
                                                                                            ├─→ MAS-107 (Shadow Mode Transition)
                                                                                            └─→ MAS-108 (4-Week Parallel Run)
                                                                                                │
                                                                                                └─→ MAS-112 (Production Cutover)
```

### External Dependency Map

| External Dependency | Affects Stories | Risk Level | Mitigation |
|--------------------|----------------|:----------:|------------|
| **ERP/SAP/Oracle API Access** | MAS-006, MAS-072 | 🔴 High | Engage IT procurement early; have offline data export as fallback |
| **MES Vendor API Availability** | MAS-007, MAS-073, MAS-049 | 🟡 Medium | Screen-scraping fallback if API not available |
| **Market Data Subscription (Bloomberg)** | MAS-015, MAS-028, MAS-095 | 🟡 Medium | Use free tier (Yahoo Finance, FRED) as interim |
| **POS/Retailer Data Feed Agreements** | MAS-008, MAS-075 | 🟡 Medium | Manual CSV upload as transition fallback |
| **EcoVadis/Sustainalytics Vendor ESG API** | MAS-032 | 🟢 Low | Manual ESG score input until API connected |
| **Banking/Payment API Integration** | MAS-059, MAS-061 | 🟡 Medium | Delayed to Phase 2-3; manual reconciliation fallback |
| **Legal/Compliance Sign-Off (Auto-Pricing)** | MAS-098 | 🔴 High | Start legal review in Phase 1; interim manual pricing approval |
| **Board-Level Sign-Off (Autonomous Ops)** | MAS-111 | 🔴 High | Monthly exec briefings starting Phase 1; phased approval increments |

---

## 8.6 Release Plan

### Release 1: "Foundation" (Sprint 1-6, Weeks 1-12)

| Sprint | Dates | Stories | SP | Theme |
|--------|-------|---------|:--:|-------|
| Sprint 1 | Jun 1-12 | MAS-001, MAS-002, MAS-003, MAS-004, MAS-005, MAS-014 | 57 | Core infrastructure + CI/CD |
| Sprint 2 | Jun 15-26 | MAS-006, MAS-007, MAS-008, MAS-009, MAS-010 | 39 | Data connectors |
| Sprint 3 | Jun 29 - Jul 10 | MAS-011, MAS-012, MAS-013, MAS-015, MAS-016 | 55 | Agent scaffold + forecast |
| Sprint 4 | Jul 13-24 | MAS-017, MAS-018, MAS-019, MAS-020, MAS-021 | 47 | Forecasting + financial |
| Sprint 5 | Jul 27 - Aug 7 | MAS-022, MAS-023, MAS-024, MAS-025, MAS-026 | 32 | Phase 1 validation |
| Sprint 6 | Aug 10-21 | (Buffer: Phase 1 remediation) | — | Remediation + gate |
| **Release 1** | **Weeks 1-12** | **26 stories** | **230** | **Phase 1 Go/No-Go** |

**Release 1 Key Milestone**: Phase 1 Gate — MAPE <18%, DQ >90%, dual-write >95%, exec sign-off

---

### Release 2: "Execution" (Sprint 7-14, Weeks 13-28)

| Sprint | Dates | Stories | SP | Theme |
|--------|-------|---------|:--:|-------|
| Sprint 7 | Aug 24 - Sep 4 | MAS-027, MAS-028, MAS-029, MAS-030, MAS-031, MAS-032 | 47 | Agent-01 Procurement |
| Sprint 8 | Sep 7-18 | MAS-033, MAS-034, MAS-035, MAS-036, MAS-037, MAS-038 | 42 | Agent-03 Inventory |
| Sprint 9 | Sep 21 - Oct 2 | MAS-039, MAS-040, MAS-041, MAS-042, MAS-043 | 42 | Agent-04 Sales |
| Sprint 10 | Oct 5-16 | MAS-044, MAS-045, MAS-046, MAS-047, MAS-048, MAS-049, MAS-116 | 60 | Agent-02 Production |
| Sprint 11 | Oct 19-30 | MAS-050, MAS-051, MAS-052, MAS-053, MAS-054, MAS-055 | 37 | HITL gates |
| Sprint 12 | Nov 2-13 | MAS-056, MAS-057, MAS-058, MAS-059, MAS-060, MAS-061 | 58 | Financial engine |
| Sprint 13 | Nov 16-27 | MAS-062, MAS-063, MAS-064, MAS-065, MAS-066, MAS-067, MAS-068 | 55 | Compliance + Risk |
| Sprint 14 | Nov 30 - Dec 11 | MAS-069, MAS-070, MAS-117, MAS-071 | 31 | Cross-agent integration |
| **Release 2** | **Weeks 13-28** | **47 stories** | **372** | **Phase 2 Go/No-Go** |

**Release 2 Key Milestone**: Phase 2 Gate — 3 product lines, HITL intervention <20%, turnover +5%, margin +1%

---

### Release 3: "Enterprise" (Sprint 15-24, Weeks 29-52)

| Sprint | Dates | Stories | SP | Theme |
|--------|-------|---------|:--:|-------|
| Sprint 15 | Dec 14 - Jan 1 | MAS-072, MAS-073, MAS-074, MAS-075, MAS-076 | 76 | Enterprise connectors |
| Sprint 16 | Jan 4-22 | MAS-077, MAS-078, MAS-079, MAS-080, MAS-081 | 63 | Multi-product onboarding |
| Sprint 17 | Jan 25 - Feb 12 | MAS-082, MAS-083, MAS-084, MAS-085, MAS-086 | 55 | Circuit breaker framework |
| Sprint 18 | Feb 15 - Mar 5 | MAS-087, MAS-088, MAS-089, MAS-090 | 42 | L3 autonomous activation |
| Sprint 19 | Mar 8-26 | MAS-091, MAS-092, MAS-093, MAS-094 | 47 | L2→L3 upgrades |
| Sprint 20 | Mar 29 - Apr 16 | MAS-095, MAS-096, MAS-097, MAS-098 | 34 | Agent-05 market upgrade |
| Sprint 21 | Apr 19 - May 7 | MAS-099, MAS-100, MAS-101, MAS-102 | 55 | Security hardening |
| Sprint 22 | May 10-28 | MAS-103, MAS-104, MAS-105, MAS-106 | 34 | Low-connectivity fallback |
| Sprint 23 | May 31 - Jun 18 | MAS-107, MAS-108, MAS-109, MAS-110 | 60 | Parallel run + training |
| Sprint 24 | Jun 21 - Jul 2 | MAS-111, MAS-112, MAS-113, MAS-114, MAS-115 | 60 | Cutover + hypercare |
| **Release 3** | **Weeks 29-52** | **45 stories** | **526** | **Production Go-Live** |

**Release 3 Key Milestone**: Production Go-Live — All success criteria met, board sign-off, legacy → monitoring

---

## 8.7 Risk-Adjusted Timeline Buffer

| Phase | Planned Duration | Buffer | Adjusted Duration | Key Risk Drivers |
|-------|:---------------:|:-----:|:----------------:|-----------------|
| Phase 1 | 12 weeks | 2 weeks (17%) | 14 weeks | ERP/MES API access delays, data quality issues |
| Phase 2 | 16 weeks | 3 weeks (19%) | 19 weeks | HITL integration complexity, compliance sign-off delays |
| Phase 3 | 24 weeks | 4 weeks (17%) | 28 weeks | Enterprise integration complexity, cutover coordination |
| **Total** | **52 weeks** | **9 weeks (17%)** | **61 weeks** | |

### Buffer Use Policy

| Buffer Type | Trigger | Decision Authority | Maximum Draw |
|-------------|---------|:-----------------:|:------------:|
| **Sprint buffer** (unplanned work within sprint) | Scope increase within sprint | Scrum Master | ≤20% of sprint capacity |
| **Phase buffer** (inter-phase delay) | Phase gate criteria not met | Steering Committee | Full allocation of phase buffer |
| **Program buffer** (critical path delay) | External dependency failure | Executive Sponsor | Full remaining buffer |

---

## 8.8 Governance & Reporting

### Ceremonies

| Ceremony | Frequency | Duration | Attendees | Purpose |
|----------|:--------:|:--------:|-----------|---------|
| **Daily Standup** | Daily | 15 min | Core team | What was done, what's next, blockers |
| **Sprint Planning** | Bi-weekly (Mon) | 4 hours | Core team + SME | Sprint backlog commitment |
| **Sprint Review** | Bi-weekly (Fri) | 2 hours | Core team + stakeholders | Demo, feedback, scope adjustments |
| **Sprint Retrospective** | Bi-weekly (Fri) | 1.5 hours | Core team | Process improvement |
| **Steering Committee** | Monthly | 1 hour | Exec sponsors + PM | Budget, timeline, phase gate decisions |
| **Risk Review** | Weekly | 30 min | PM + Tech leads | Risk register update, mitigation actions |

### Reporting Artifacts

| Artifact | Frequency | Audience | Format |
|----------|:--------:|----------|--------|
| **Sprint Burndown** | Daily | Core team | Jira dashboard |
| **Sprint Report** | Bi-weekly | Stakeholders | 1-pager (done/in-progress/risks) |
| **Phase Gate Checklist** | Per gate | Steering Committee | Checklist with sign-off |
| **KPI Dashboard** | Real-time | All | Grafana |
| **Cost-Benefit Report** | Monthly | CFO + Steering Committee | Structured report |
| **Risk Register** | Weekly | PM + Tech leads | Spreadsheet/Jira |

---

## 8.9 Quick-Reference: Story Point to Effort Mapping

| Story Points | Effort (Ideal Person-Days) | Complexity | Typical Story |
|:-----------:|:--------------------------:|:----------:|---------------|
| 1 | 1-2 hours | Trivial | Config change, documentation update |
| 3 | 1-2 days | Low | Single endpoint, simple rule, dashboard panel |
| 5 | 3-4 days | Medium | Feature with 1-2 acceptance criteria |
| 8 | 5-7 days | Medium-High | Feature with 3-5 acceptance criteria |
| 13 | 10-14 days (2 sprint max) | High | Complex feature, integration work |
| 21 | 15-20 days | Very High | Epic-level, multiple components, external dependency |
| 34+ | Should be split | — | Break down into smaller stories |

---

## 8.10 Delivery Checklist (Master Tracking)

### Phase 1 Gate (Week 12 ✓ / Week 14 Adjusted)

- [ ] MAPE <18% on pilot product line (4 consecutive weeks)
- [ ] Data quality pass rate >90% across all sources
- [ ] Dual-write reconciliation >95% match rate
- [ ] System latency <5s for critical path
- [ ] All 9 agents scaffolded and running (advisory mode)
- [ ] Security baseline controls implemented (mTLS, Vault, RBAC)
- [ ] HITL gate framework designed and approved
- [ ] Phase 1 ROI validated (>$200K inventory savings)
- [ ] CPO, COO, CTO sign-off obtained

### Phase 2 Gate (Week 28 ✓ / Week 31 Adjusted)

- [ ] MAPE <15% for 3 product lines (8 consecutive weeks)
- [ ] Data quality pass rate >95%
- [ ] Dual-write reconciliation >99% match rate
- [ ] System latency <2s for critical path
- [ ] Human intervention rate <20% for L2 agents
- [ ] HITL gates operational and tested (>100 approval flows)
- [ ] SOX/ISO controls automated and verified
- [ ] Phase 2 ROI validated (>$3M annualized benefit)
- [ ] Board-level sign-off for autonomous operations

### Phase 3 Go-Live Gate (Week 52 ✓ / Week 61 Adjusted)

- [ ] All success criteria met: MAPE <12%, inventory turnover +15%, margin +5-8%, fulfillment >98%
- [ ] Enterprise data quality >99% pass rate
- [ ] Circuit breaker framework operational (all 3 tiers)
- [ ] Zero-trust architecture deployed (mTLS, OPA, Vault, RBAC)
- [ ] Low-connectivity fallback validated
- [ ] 4-week parallel run completed: >99.9% match rate
- [ ] Human intervention rate <5% in final week
- [ ] All training completed (all user roles)
- [ ] Board-level sign-off obtained
- [ ] Legacy → monitoring-only transition complete

---

*See also: [Implementation Roadmap](./04-implementation-roadmap.md) | [Risk Register](./05-risk-register.md) | [Evaluation Framework](./07-evaluation-framework.md)*
