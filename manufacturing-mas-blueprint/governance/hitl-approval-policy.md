# HITL Approval Policy v1.0

> **Document Owner**: Chief Technology Officer (CTO)  
> **Classification**: Internal — Confidential  
> **Status**: Draft for Review  
> **Last Updated**: 2026-05-21  
> **Next Review**: 2026-08-21 (quarterly)  
> **Version**: 1.0.0

---

## Executive Summary

This document defines the **Human-in-the-Loop (HITL) Approval Policy** for the Manufacturing Multi-Agent System (MAS). It establishes the governance framework governing when, how, and by whom human approval is required before the autonomous system may execute decisions. This policy applies to all 9 agents operating across procurement, production, inventory, sales, market intelligence, predictive analytics, financial accounting, compliance, and orchestration domains.

The objective is to balance **operational autonomy** with **risk control** — ensuring that decisions with material financial, compliance, safety, or reputational impact are subject to human judgment, while routine operations proceed without human bottleneck.

**Policy Owner**: CTO  
**Signatories Required**: CFO, COO, CPO, CSO, CRO/CCO, Legal Counsel, CEO

---

## 1. Purpose and Scope

### 1.1 Purpose

This policy establishes:

1. The **autonomy framework** defining three tiers of agent independence
2. **Mandatory HITL scenarios** — decisions that always require human approval
3. **Decision authority matrix** — who is authorized to approve each decision type
4. **SLA requirements** — response time commitments per priority level
5. **Escalation protocols** — what happens when SLAs are breached
6. **Audit and compliance** — immutable record-keeping requirements
7. **Emergency procedures** — override protocols for business continuity

### 1.2 Scope

**In Scope:**
- All 9 agents (Agent-01 through Agent-09) in all operational phases
- All decisions with financial value >$50K, compliance impact, or safety relevance
- All system-to-human escalations regardless of communication channel
- All override decisions where a human countermands an agent recommendation

**Out of Scope:**
- Strategic investment decisions outside the system's operational mandate
- Board-level governance and corporate strategy
- Customer-facing pricing communication (handled by Sales & Distribution policy)

---

## 2. Governance Principles

### 2.1 Core Tenets

| # | Principle | Description |
|---|-----------|-------------|
| 1 | **Autonomy by Default, HITL by Exception** | Agents operate at their assigned autonomy level unless a threshold is breached |
| 2 | **Proportional Control** | The rigor of HITL gates scales with decision impact (financial value, compliance risk, safety) |
| 3 | **Deterministic Financials** | All financial calculations (COGS, margin, P&L) are rule-based and auditable — AI only forecasts and recommends |
| 4 | **Explainable Decisions** | Every agent recommendation must include reasoning, confidence score, data sources, alternatives, and business impact estimate |
| 5 | **Immutable Audit Trail** | All HITL decisions, regardless of outcome, are logged to WORM storage with full context |
| 6 | **Right to Override** | Authorized humans may override any agent decision at any time, with reason recorded |
| 7 | **Safety First** | No autonomous action affecting safety-critical systems, payroll, tax filings, or customer contracts |

### 2.2 Autonomy Tier Definitions

| Tier | Code | Name | Description | Human Role | Default Phase |
|------|------|------|-------------|-----------|---------------|
| 1 | L1 | **Advisory** | Agent analyzes, recommends, and presents options with supporting evidence | Required approver for all actions | Phase 1 (0-3mo) |
| 2 | L2 | **Semi-Autonomous** | Agent executes within defined policy bounds; escalates when thresholds exceeded | Monitor with override capability; mandatory HITL for defined triggers | Phase 2 (3-6mo) |
| 3 | L3 | **Full Autonomous** | Agent executes fully within bounds; only escalates on errors, conflicts, or circuit-breaker conditions | Exception-only monitoring | Phase 3 (6-12mo) |

### 2.3 Phase-Based Autonomy Migration

| Agent | Phase 1 | Phase 2 | Phase 3 | Gate Criteria for Promotion |
|-------|---------|---------|---------|-----------------------------|
| Agent-01 Procurement | **L1** Advisory | **L2** Semi-Autonomous | **L2** Semi-Autonomous | MAPE <18%, human override rate <20%, 30-day pilot |
| Agent-02 Production | **L1** Advisory | **L1**→**L2** (mo. 5) | **L2** Semi-Autonomous | OEE stable >80%, zero safety incidents, >95% schedule adherence |
| Agent-03 Inventory | **L1** Advisory | **L2** Semi-Autonomous | **L3** Full Autonomous | No stock-outs in 60 days, dead stock <3% of value |
| Agent-04 Sales | **L1** Advisory | **L2** Semi-Autonomous | **L2** Semi-Autonomous | Fulfillment rate >97%, customer satisfaction stable |
| Agent-05 Market | **L1** Advisory | **L1** Advisory | **L2** Semi-Autonomous | Forecast accuracy MAPE <15%, zero pricing compliance incidents |
| Agent-06 Predictive | **L1** Advisory | **L1** Advisory | **L1** Advisory | Permanent L1 (forecasts always reviewed before action) |
| Agent-07 Financial | **L1** Read-only | **L2** Semi-Autonomous | **L2** Semi-Autonomous | SOX controls passing >99%, zero financial close errors |
| Agent-08 Compliance | **L1** Monitor | **L3** Full Autonomous | **L3** Full Autonomous | Compliance coverage >95%, false positive rate <5% |
| Agent-09 Orchestrator | **L2** Semi-Autonomous | **L3** Full Autonomous | **L3** Full Autonomous | All agent health metrics green for 30 consecutive days |

---

## 3. Roles, Responsibilities & Authorities

### 3.1 HITL Decision Authority Matrix (RACI)

| Decision Type | Proposed By | Recommended Approver | Secondary Approver | Tertiary (Escalation) | Inform |
|---------------|-------------|---------------------|-------------------|----------------------|--------|
| Pricing change >5% | Agent-04 | CSO / Pricing Committee | CFO | CEO | Sales Ops |
| Pricing change 2-5% | Agent-04 | Sales Director | CSO | CFO | - |
| Production schedule shift >8h | Agent-02 | Production Manager | COO | CEO | Supply Chain |
| Production schedule shift 2-8h | Agent-02 | Shift Supervisor | Production Manager | COO | - |
| New supplier onboarding >$500K/yr | Agent-01 | CPO / Sourcing Director | CFO | CEO | Legal |
| New supplier onboarding <$500K/yr | Agent-01 | Sourcing Manager | CPO | CFO | - |
| PO value >$500K | Agent-01 | Procurement Director | CPO | CFO | Finance |
| PO value $100K-$500K | Agent-01 | Procurement Manager | Procurement Director | - | - |
| Financial closing adjustment >$50K | Agent-07 | CFO / Controller | Audit Committee | CEO | Board |
| Financial closing adjustment $10K-$50K | Agent-07 | Controller | CFO | - | Internal Audit |
| Budget override >5% | Agent-07 | CFO | CEO | Board | Finance |
| Budget override 2-5% | Agent-07 | Finance Director | CFO | - | - |
| Compliance violation (SOX/regulatory) | Agent-08 | CCO / Legal Counsel | CEO | Board | Audit Committee |
| Compliance violation (internal policy) | Agent-08 | Compliance Officer | CCO | CEO | - |
| Circuit breaker reset | Agent-09 | CTO / System Architect | CIO | CEO | All Agents |
| Model deployment to production | Agent-09 | ML Engineering Lead | CTO | CIO | Compliance |
| Inventory reallocation >$200K impact | Agent-03 | Supply Chain Director | COO | CFO | Finance |
| Inventory reallocation <$200K | Agent-03 | Warehouse Manager | Supply Chain Director | - | - |
| Hedge activation | Agent-01 | Treasurer / CFO | CEO | Board | Finance |
| Market intelligence auto-signal (Phase 3) | Agent-05 | CMO / Legal Counsel | CEO | Board | Compliance |
| Emergency system halt | Any Agent | On-call Engineer | CTO | CIO | CRO |

### 3.2 Role Definitions

| Role | Typically Held By | Authority Level | HITL Decision Authority | SLA Responsibility |
|------|-------------------|-----------------|------------------------|-------------------|
| **L1 - Operator** | Analyst, Supervisor, Shift Lead | Can approve within standard operating parameters | Up to $50K value, no compliance/safety impact | Acknowledge within 2h |
| **L2 - Manager** | Department Manager, Director | Can approve within department policy | Up to $500K value, standard exceptions | Respond within 1h |
| **L3 - Executive** | VP, C-level Officer | Can approve all except board-level decisions | Unlimited value, compliance/safety overrides | Respond within 30min |
| **L4 - Board** | Board of Directors | Strategic decisions, major capital allocation | Structural changes, M&A implications, policy amendments | Convene within 24h |

### 3.3 Delegation of Authority

- Approvers may formally delegate authority to a named alternate in writing (email or policy system)
- Delegation expires after 90 days unless renewed
- Delegation does not transfer accountability — the original approver remains responsible
- During absences (vacation, illness), the escalation path automatically activates

---

## 4. Mandatory HITL Scenarios

### 4.1 Threshold Matrix

The following table defines **every scenario** that triggers a mandatory HITL approval gate, organized by agent.

| ID | Agent | Trigger Condition | Threshold | Priority | Approver | SLA | Fallback |
|----|-------|-------------------|-----------|----------|----------|-----|----------|
| H-001 | Agent-01 | Price spike (raw material) | >5% movement in 24h | P2-Medium | CPO | 4h | Use cached prices +3% buffer |
| H-002 | Agent-01 | Price spike (critical) | >10% movement in 24h | P1-High | CFO + CPO | 1h | Halt procurement; use safety stock |
| H-003 | Agent-01 | PO value threshold | >$500K single PO | P1-High | Procurement Director | 1h | Split PO into <$500K tranches |
| H-004 | Agent-01 | Vendor score low | <60/100 composite score | P2-Medium | Sourcing Team | 4h | Auto-reject vendor; use incumbent |
| H-005 | Agent-01 | Sole-source procurement | 0 alternative vendors qualified | P1-High | CPO | 1h | Extend incumbent contract |
| H-006 | Agent-01 | New supplier onboarding | Annual value >$500K | P2-Medium | CPO + Sourcing Director | 24h | Delay onboarding; use existing |
| H-007 | Agent-01 | Contract term deviation | Terms outside standard ±10% | P2-Medium | Legal Counsel | 24h | Use standard terms template |
| H-008 | Agent-01 | ESG compliance flag | Vendor ESG score below minimum | P2-Medium | CPO + Sustainability Officer | 48h | Flag for review; do not onboard |
| H-009 | Agent-02 | Production schedule override | Change >8 hours from plan | P2-Medium | Production Manager | 2h | Use conservative default schedule |
| H-010 | Agent-02 | Quality defect rate | >5% defect rate on any line | P1-High | QA Director | 1h | HALT production line |
| H-011 | Agent-02 | OEE critical drop | <70% for 2 consecutive shifts | P1-High | Operations Manager | 1h | Switch to maintenance mode |
| H-012 | Agent-02 | Predictive maintenance alert | Failure confidence >0.95 | P1-High | Maintenance Manager | 30min | Immediate halt + manual inspection |
| H-013 | Agent-02 | Safety interlock trigger | MES safety system alert | P0-Critical | Safety Officer | 5min | IMMEDIATE HALT — no override |
| H-014 | Agent-03 | Stock-out probability | >15% within lead time | P1-High | Supply Chain Director | 1h | Emergency expedite + CPO alert |
| H-015 | Agent-03 | Dead stock write-off | >5% of total inventory value | P2-Medium | Finance Director | 24h | Flag; hold for quarterly review |
| H-016 | Agent-03 | Space utilization critical | >92% warehouse capacity | P2-Medium | Warehouse Manager | 4h | Redirect to overflow facility |
| H-017 | Agent-04 | Pricing change (major) | >5% from current price | P1-High | CSO / Pricing Committee | 1h | No change; re-evaluate in 24h |
| H-018 | Agent-04 | Pricing change (moderate) | 2-5% from current price | P2-Medium | Sales Director | 4h | Auto-approve with trend monitoring |
| H-019 | Agent-04 | Customer allocation change | Tier-1 customer allocation <100% | P1-High | CSO | 1h | Maintain current allocation |
| H-020 | Agent-04 | Bulk order discount | >10% discount on single order | P2-Medium | Sales Director | 4h | Standard discount only |
| H-021 | Agent-04 | Returns exception | Outside standard return policy | P2-Medium | Customer Service Manager | 4h | Deny; route to manual process |
| H-022 | Agent-05 | Competitive price signal | Competitor price change >5% | P2-Medium | CMO | 4h | Flag for review; no auto-response |
| H-023 | Agent-05 | Market disruption alert | Macro event (e.g., sanctions, tariffs) | P1-High | CPO + CFO | 1h | Activate disruption playbook |
| H-024 | Agent-05 | Sentiment shift | Customer sentiment drop >15% | P2-Medium | CMO | 4h | Increase monitoring frequency |
| H-025 | Agent-06 | Forecast revision (major) | >20% revision from previous forecast | P1-High | CPO | 1h | Use previous forecast + conservative buffer |
| H-026 | Agent-06 | Forecast confidence low | Confidence interval <60% | P2-Medium | Demand Planning Lead | 4h | Use ensemble average |
| H-027 | Agent-06 | Model drift detected | PSI >0.2 or KS-test >0.25 | P2-Medium | ML Engineering Lead | 4h | Rollback to last known-good model |
| H-028 | Agent-07 | COGS variance | >3% from standard cost | P1-High | CFO | 1h | Flag variance; close with note |
| H-029 | Agent-07 | Gross margin alert | Margin drops below target threshold | P1-High | CFO | 1h | Alert CEO; activate margin recovery plan |
| H-030 | Agent-07 | Budget variance | >5% from approved budget | P2-Medium | CFO | 24h | Flag; no action until approved |
| H-031 | Agent-07 | Cash flow projection shortfall | >$1M negative variance next 30 days | P1-High | CFO + Treasurer | 1h | Activate credit line; defer discretionary spend |
| H-032 | Agent-07 | Financial close adjustment | >$50K adjustment required | P2-Medium | CFO / Controller | 4h | Carry forward; close with note |
| H-033 | Agent-08 | SOX control failure | Automated control test fails | P1-High | CCO | 1h | HALT affected process; manual control |
| H-034 | Agent-08 | Regulatory change alert | New regulation requiring process change | P2-Medium | CCO + Legal Counsel | 48h | Assess impact; implement within mandated timeline |
| H-035 | Agent-08 | Data subject request (GDPR/CCPA) | Agent processes personal data | P2-Medium | DPO | 24h | Quarantine data; manual fulfillment |
| H-036 | Agent-08 | Supply disruption detected | >2σ lead-time variance | P1-High | CPO | 1h | Activate alt-source playbook |
| H-037 | Agent-08 | Cybersecurity alert | Anomaly detected in agent behavior | P1-High | CISO | 30min | Isolate agent; forensic investigation |
| H-038 | Agent-09 | Cross-agent conflict | Conflict unresolved after 2 arbitration rounds | P2-Medium | CTO | 4h | Pause conflicting actions; manual override |
| H-043 | Agent-05 | Seasonality pattern shift | Holiday/seasonal demand >3σ from historical pattern | P2-Medium | Demand Planning Lead | 4h | Use 3-year seasonal average |
| H-044 | Agent-05 | Social sentiment escalation | Brand sentiment drop >20% in 24h period | P1-High | CMO | 2h | Pause automated marketing; manual review |
| H-045 | Agent-05 | Trend anomaly detection | Google Trends/social volume spike >3σ unexplained | P2-Medium | Market Intelligence Lead | 4h | Flag for analyst review before action |
| H-046 | Agent-06 | Scenario simulation validation | New scenario parameters outside historical bounds ( >2σ) | P2-Medium | Demand Planning Lead | 4h | Use conservative scenario (closest historical analog) |
| H-047 | Agent-06 | What-if analysis approval | What-if analysis affects >$500K inventory commitment | P2-Medium | CPO | 4h | Revert to base forecast |
| H-039 | Agent-09 | Circuit breaker trip | KPI threshold breached | P1-High | CTO | 30min | All agents → L1 (Advisory) |
| H-040 | Agent-09 | Model deployment to production | New model version ready | P3-Low | ML Engineering Lead | 48h | Keep previous model |
| H-041 | Agent-09 | Agent health critical | Agent unresponsive >5min | P1-High | On-call Engineer | 15min | Restart agent; fallback if persistent |
| H-042 | Agent-09 | System-wide rollback | Performance degradation >20% | P1-High | CTO | 30min | Rollback to last known-good configuration |

### 4.2 HITL Threshold Decision Tree

```
┌─────────────────────────────────────┐
│        DECISION ENCOUNTERED          │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   CHECK: Is this a defined HITL     │
│   scenario? (Section 4.1 Matrix)    │
└──────────┬──────────────────────────┘
           │                  │
         YES                  NO
           │                  │
           ▼                  ▼
┌──────────────────┐  ┌─────────────────────────┐
│  CREATE HITL     │  │  CHECK: Within agent     │
│  TICKET          │  │  autonomy bounds?        │
│  • Priority      │  └──────────┬───────────────┘
│  • SLA start     │             │          │
│  • Escalation    │           YES          NO
│  • Notification  │             │          │
└────────┬─────────┘             ▼          ▼
         │              ┌────────────────┐ ┌──────────────────┐
         ▼              │ AUTO-EXECUTE   │ │ CREATE HITL      │
┌──────────────────┐    │ • Log decision │ │ TICKET           │
│  WAIT FOR        │    │ • Publish      │ │ (policy limit    │
│  HUMAN DECISION  │    │   event        │ │  exceeded)       │
│  (SLA timer)     │    │ • Agent        │ └──────────────────┘
└────────┬─────────┘    │   continues    │
         │              └────────────────┘
         ▼
┌─────────────────────────────────────┐
│  RESPONSE RECEIVED?                 │
│  ┌──── YES ────┐  ┌─── NO (SLA) ─┐ │
│  │             │  │              │ │
│  ▼             │  ▼              │ │
│  Process       │  ESCALATE       │ │
│  decision      │  to next level  │ │
│  • Approve     │  Reset SLA      │ │
│  • Reject      │  Notify chain   │ │
│  • Override    │  Continue wait  │ │
└─────────────────────────────────────┘
```

---

## 5. HITL Ticket Lifecycle & Workflow

### 5.1 Ticket States

```
                  ┌─────────────┐
                  │   CREATED    │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
            ┌────▶│  NOTIFIED   │◀────────────┐
            │     └──────┬──────┘              │
            │            │                     │
            │            ▼                     │
            │     ┌─────────────┐              │
            │     │   REVIEW    │              │
            │     └──────┬──────┘              │
            │            │                     │
            │     ┌──────┴──────┐              │
            │     │             │              │
            │     ▼             ▼              │
            │  ┌────────┐  ┌────────┐         │
            │  │DECISION│  │ TIMEOUT│─────────┘
            │  │ MADE   │  │ (SLA)  │  escalate
            │  └───┬────┘  └────────┘
            │      │
            │      ▼
            │  ┌──────────┐
            │  │ EXECUTED │
            │  └────┬─────┘
            │       │
            │       ▼
            │  ┌──────────┐
            └──│  CLOSED  │
               └──────────┘
```

### 5.2 Ticket Lifecycle Steps

**Step 1: CREATED**
- Trigger condition detected by agent
- Agent generates HITL ticket with full context:
  - Ticket ID (format: `H-YYYY-NNNN`)
  - Decision type and trigger value
  - Agent recommendation with confidence score
  - Business impact estimate ($ amount, margin impact)
  - Data sources and provenance
  - Alternatives considered
  - Relevant historical context (last 3 similar decisions)
- Ticket persisted to database and WORM audit log

**Step 2: NOTIFIED**
- Approver(s) notified via configured channel:
  - **P0-Critical**: SMS + phone call + Slack/Teams dashboard alert
  - **P1-High**: Slack/Teams rich card with decision buttons + email
  - **P2-Medium**: Slack/Teams notification + email digest
  - **P3-Low**: Email digest + dashboard queue
- SLA timer starts
- Escalation chain pre-configured (Primary → Secondary → Tertiary)

**Step 3: REVIEW**
- Approver opens ticket in HITL dashboard (or mobile app)
- Dashboard presents:
  - Decision summary (1 sentence)
  - Impact visualization (before/after, trend, P&L effect)
  - Agent recommendation with confidence
  - Alternatives ranked with trade-offs
  - Data source links (traceable to source system)
  - Historical pattern (how similar decisions performed)
- Approver can:
  - Request additional analysis from agent (within 15-minute SLA pause)
  - View raw data
  - Consult with subject matter experts via threaded comments
  - Compare with similar past decisions

**Step 4: DECISION**

| Decision | Action | System Response |
|----------|--------|----------------|
| **Approve** | Human clicks "Approve" | Agent executes recommendation; result logged |
| **Reject** | Human clicks "Reject" + reason | No action taken; logged with reason; agent notified |
| **Modify/Override** | Human provides parameter changes | Agent re-executes with modified parameters; new recommendation presented |
| **Defer** | Human sets reminder for later | SLA extended by defined duration; status remains PENDING |
| **Escalate** | Human clicks "Escalate" | Ticket routed to next authority level; SLA resets |
| **Request Info** | Human asks for more analysis | Agent performs additional analysis (15-min max); ticket updated |

**Step 5: CLOSED**
- Decision execution confirmed by agent
- Full decision package written to immutable audit log:
  - Input snapshot (trigger conditions, data used)
  - Agent recommendation (model version, confidence, alternatives)
  - Human decision (who, what, when, why)
  - Outcome (executed parameters, actual result when available)
- Feedback sent to ML pipeline for model improvement
- HITL trend analysis updated (override patterns, SLA compliance, approver workload)

### 5.3 SLA Requirements

| Priority | Definition | Target Response | SLA Deadline | Escalation Trigger | Escalation Path |
|----------|-----------|-----------------|-------------|-------------------|-----------------|
| **P0-Critical** | Immediate safety/compliance risk; system halt | 5 minutes | 15 minutes | Missed at T+5min | Primary (On-call) → T+5: Secondary (Manager) → T+10: Tertiary (VP/CISO/CTO) |
| **P1-High** | Significant financial/operational impact; regulatory | 15 minutes | 1 hour \* | Missed at T+15min | Primary (Director) → T+30: Secondary (VP) → T+45: Tertiary (C-level) |
| **P2-Medium** | Moderate impact; needs human judgment | 1 hour | 4 hours | Missed at T+1h | Primary (Manager) → T+2h: Secondary (Director) → T+3h: Tertiary (VP) |
| **P3-Low** | Minor optimization; fine-tuning | 4 hours | 24 hours | Missed at T+4h | Primary (Analyst) → T+12h: Secondary (Manager) → T+18h: Tertiary (Director) |
| **P4-Info** | Informational; no decision required | 24 hours | N/A | N/A | N/A — no escalation needed |

> \* **Exception**: H-037 (Cybersecurity alert) and H-039 (Circuit breaker trip) have **30-minute SLA** due to critical security/system stability implications. These are justified deviations from the standard 1-hour P1-High SLA.

| Metric | Target | Measurement | Reporting |
|--------|--------|-------------|-----------|
| P0-Critical response within 5 min | **>99.5%** | System timestamp of ticket creation → first response | Real-time dashboard |
| P1-High resolved within SLA | **>95%** | Ticket created → approved/rejected/escalated | Weekly ops review |
| P2-Medium resolved within SLA | **>90%** | Ticket created → approved/rejected/escalated | Weekly ops review |
| P3-Low resolved within SLA | **>85%** | Ticket created → approved/rejected/escalated | Monthly review |
| Average response time (P1) | **<30 minutes** | Mean time to human acknowledgment | Real-time dashboard |
| Overdue ticket ratio | **<5%** | Tickets exceeding SLA / total tickets | Daily alert if breached |

### 5.5 Communication Channels

| Channel | Priority | Format | Retry Policy | Fallback |
|---------|----------|--------|-------------|----------|
| **HITL Dashboard** | All | Interactive panel with accept/reject/modify buttons | N/A — persistent | Mobile-responsive web app |
| **Slack / Teams** | P0, P1, P2 | Rich card with decision actions + impact summary | 3 retries (5 min apart) | SMS notification |
| **Email** | P2, P3, P4 | Summary with deep link to dashboard | 2 retries (1 hour apart) | Dashboard notification |
| **SMS** | P0, P1 | Alert with ticket ID, priority, and link | Every 5 min × 3 | Phone call |
| **Phone Call** | P0 only | Automated voice alert (PagerDuty/OpsGenie) | Call once | SMS every 5 min |
| **Mobile Push** | P0, P1, P2 | Native notification with quick actions | Interval dependent on priority | Email |

---

## 6. Emergency Protocols

### 6.1 System Halt Procedure

In the event of a critical failure, compliance violation, or safety incident, **any authorized individual** may trigger a system halt:

```
┌─────────────────────────────────────────────┐
│          EMERGENCY HALT PROCEDURE             │
├─────────────────────────────────────────────┤
│                                               │
│  TRIGGER (any of):                           │
│  • Safety interlock from MES                  │
│  • Agent-08 detects SOX/regulatory violation  │
│  • CISO orders halt due to security breach    │
│  • COO/CTO invokes manual halt                │
│  • Circuit breaker trips (3 strikes)          │
│                                               │
│  ACTIONS:                                     │
│  1. All agents → L1 (Advisory) immediately    │
│  2. All pending automated actions → HOLD      │
│  3. Orchestrator logs incident #INC-XXXX      │
│  4. HITL ticket created (P0-Critical)         │
│  5. CTO/CISO/CRO notified via SMS + call      │
│  6. Legacy systems resume full control        │
│  7. Root cause investigation auto-triggered   │
│                                               │
│  RESUMPTION:                                  │
│  • Requires CTO + CRO sign-off                │
│  • Gradual re-escalation: L1 → L2 after      │
│    24h of stable operation                    │
│  • Full autonomy only after 7 days monitoring │
└─────────────────────────────────────────────┘
```

### 6.2 Low-Connectivity Fallback

When the system detects degraded network connectivity to external services:

| Condition | Agent Behavior | Human Role | Recovery |
|-----------|---------------|-----------|----------|
| Kafka unavailable | Local file queue; replay on reconnect | Monitor dashboard for queue size | Automatic on reconnect |
| External data source unavailable | Cached data (max 24h old) + conservative buffer | Review cache freshness | Automatic on reconnect |
| Database unavailable | In-memory cache with periodic flush attempts | HITL tickets queued locally | Automatic on DB restore |
| Full isolation (>30min) | Agents revert to L1; action queue with HITL markers | Manual approval of queued actions | Manual review of queue |
| Extended outage (>4h) | Legacy system takeover (parallel run protocol) | Manual operations resume | Manual cutover |

### 6.3 Parallel Run Protocol (Phase 1-2)

During the migration period, the legacy ERP/MES system continues running alongside the MAS:

```
┌────────────────────────────────────────────────┐
│          DUAL-WITE PARALLEL RUN PROTOCOL        │
├────────────────────────────────────────────────┤
│                                                  │
│  DATA FLOW:                                      │
│  ┌──────────┐     ┌──────────┐     ┌─────────┐ │
│  │  Legacy  │────▶│Reconcil. │◀────│   MAS   │ │
│  │  System  │     │  Engine  │     │ Agents  │ │
│  └──────────┘     └──────────┘     └─────────┘ │
│                                                  │
│  RECONCILIATION:                                 │
│  • Every action by MAS is also sent to legacy    │
│  • Reconciliation job runs every 4 hours         │
│  • Discrepancies flagged for human review        │
│  • >99% match rate required for phase promotion  │
│                                                  │
│  FALLBACK:                                       │
│  • If reconciliation error >5%, revert to legacy │
│  • MAS enters read-only mode                     │
│  • HITL created for reconciliation failure       │
└──────────────────────────────────────────────────┘
```

---

## 7. Audit, Compliance & Accountability

### 7.1 Immutable Audit Trail Requirements

Every HITL decision produces an audit record containing:

| Field | Requirement | Format |
|-------|-------------|--------|
| Ticket ID | Unique, sequential | `H-YYYY-NNNN` (e.g., H-2026-0042) |
| Timestamp | NTP-synchronized, UTC | ISO 8601 with timezone |
| Agent ID | Source agent identifier | `agent-0X` |
| Decision Type | From Section 4 matrix | Enum value |
| Trigger Value | Exact value that breached threshold | Float / string |
| Agent Recommendation | Full recommendation text | JSON-LD |
| Model Version | MLflow registered model version | Semver + git hash |
| Confidence Score | 0.0 - 1.0 | Float |
| Data Sources | All sources used in analysis | Array of URIs |
| Alternatives Considered | Minimum 2 alternatives | Array of JSON objects |
| Business Impact Estimate | $ amount, margin impact | JSON |
| Human Decision | Approve / Reject / Override / Escalate | Enum |
| Decision Rationale | Human-entered reason | Free text (min 10 chars for reject) |
| Approver Identity | Authenticated user identifier | LDAP/SSO UPN |
| Approval Channel | Dashboard / Slack / SMS / API | Enum |
| SLA Metrics | Created → Notified → Decision timestamps | ISO 8601 |
| Escalation History | All escalation steps with timestamps | Array |
| Outcome | Executed result + actual vs. projected | JSON |

### 7.2 WORM Storage Requirements

| Requirement | Specification |
|-------------|---------------|
| Storage type | Write-Once, Read-Many (WORM) |
| Retention period | 7 years (SOX requirement), 10 years (recommended) |
| Encryption | AES-256 at rest |
| Access logging | All reads logged with user identity, timestamp, purpose |
| Deletion policy | Immutable — no deletion possible within retention period |
| Backup | Geo-redundant copy in secondary region |
| Audit access | Read-only via API with full access logging |

### 7.2.5 Conflict Resolution → HITL Mapping

The following table maps each conflict pattern (defined in `conflict-resolution.md`) to the corresponding HITL scenario in this policy. This ensures that when a cross-agent conflict is detected, the correct escalation path is activated.

| Conflict ID | Conflict Pattern | HITL Scenario ID | Approver | Trigger Condition |
|-------------|-----------------|------------------|----------|------------------|
| C-01 | Inventory Agent reduction vs. Sales Agent demand spike | H-014 (stock-out) + H-025 (forecast revision) | Supply Chain Director + CPO | Cost of stock-out vs. cost of holding gap >$100K |
| C-02 | Procurement alt supplier vs. Financial higher cost | H-006 (supplier onboarding) + H-028 (COGS variance) | CPO + CFO | TCO gap >5% |
| C-03 | Production schedule change vs. Sales committed orders | H-009 (schedule override) | Production Manager + CSO | Any committed order affected |
| C-04 | Forecast demand drops vs. Procurement PO already placed | H-025 (forecast revision) + H-003 (PO value) | CPO | PO value >$250K |
| C-05 | Market price war signal vs. Sales hold price | H-017 (pricing >5%) | CSO / Pricing Committee | Margin impact >2% |
| C-06 | Compliance violation vs. Operations continue | H-033 (SOX control failure) | CCO | IMMEDIATE HALT — compliance always wins |
| C-07 | Financial negative margin vs. Sales fulfill order | H-029 (per-order or period margin alert) | CFO | Negative margin confirmed on any order or period |
| C-08 | Predictive build inventory vs. Finance conserve cash | H-031 (cash flow shortfall) | CFO | Cash impact >$500K |

---

### 7.3 Segregation of Duties (SoD)

The system enforces the following Segregation of Duties rules at the architecture level:

| Rule | Description | Enforcement |
|------|-------------|-------------|
| **SoD-01** | No single agent creates and approves a financial transaction | Agent-07 recommends → Orchestrator routes to HITL → Finance approver signs |
| **SoD-02** | No single agent can modify both price and production schedule | Agent-04 (pricing) and Agent-02 (production) are separate agents with independent governance |
| **SoD-03** | Compliance monitoring is independent of execution | Agent-08 (Compliance) reports to CRO, not COO or CFO |
| **SoD-04** | Forecast creation is independent of forecast consumption | Agent-06 (Predictive) creates forecasts; Agents 01-04 consume them; Agent-09 validates |
| **SoD-05** | Supplier onboarding requires separate procurement and finance approval | Agent-01 screens → CPO approves → Finance validates payment terms |
| **SoD-06** | System operations and security monitoring are separate | CTO (operations) vs. CISO (security) — independent reporting lines |

### 7.4 SOX Control Mapping

The following SOX-relevant controls are automated in the HITL system:

| Control ID | SOX Requirement | HITL Implementation |
|------------|-----------------|---------------------|
| SOX-01 | Segregation of duties | Enforced via agent architecture (SoD rules above) |
| SOX-02 | Access controls | RBAC + mTLS + HashiCorp Vault |
| SOX-03 | Audit trail completeness | WORM storage for all HITL decisions |
| SOX-04 | Financial close controls | All >$50K adjustments require HITL (H-032) |
| SOX-05 | Revenue recognition | Agent-07 uses deterministic rules; no AI in revenue calculation |
| SOX-06 | Journal entry controls | All system-generated journal entries require HITL approval |
| SOX-07 | Period-end reporting | Agent-07 generates reports; CFO reviews changes >5% variance |
| SOX-08 | IT general controls | System change management via Agent-09 + CTO approval (H-040) |

### 7.5 Compliance Dashboard Metrics

| Metric | Target | Report Frequency | Audience |
|--------|--------|-----------------|----------|
| HITL SLA compliance rate | >95% on P0-P1 | Real-time | CTO, COO |
| Override rate (human vs. agent) | <15% | Weekly | CPO, CSO, CFO |
| Audit trail completeness | 100% | Daily | CCO, Internal Audit |
| Segregation of duty violations | 0 | Real-time | CCO |
| SOX control pass rate | >99% | Daily | CFO, CCO |
| HITL decision accuracy (actual vs. projected) | >90% | Monthly | All stakeholders |
| Time to resolution (mean) | <30min P0, <45min P1 | Weekly | CTO |
| Escalation rate | <10% | Monthly | CTO |
| False positive HITL triggers | <5% | Weekly | ML Engineering |

---

## 8. Exception Process

### 8.1 Requesting a Policy Exception

Decisions falling outside the defined policy may be submitted for exception:

1. **Submitter**: Any stakeholder (agent owner, business lead, or system operator)
2. **Format**: Formal exception request via HITL dashboard or email to CTO
3. **Required Fields**:
   - Decision details and context
   - Why standard policy cannot be followed
   - Proposed alternative approach
   - Risk assessment of exception
   - Business justification (expected benefit vs. risk)
   - Duration (one-time vs. time-bound vs. permanent)
4. **Review**: CTO + relevant C-level (CFO for financial, CCO for compliance, etc.)
5. **Decision**: Approved / Rejected / Modified — within 5 business days
6. **Logging**: Exception logged to WORM storage with full rationale
7. **Expiration**: All exceptions auto-expire; permanent exceptions require annual re-approval

### 8.2 Emergency Exception

In genuine emergencies where following the standard process would cause harm:
- Verbal approval from CTO + relevant C-level is sufficient
- Written confirmation must follow within 24 hours
- Emergency exceptions automatically expire after 7 days

---

## 9. Policy Governance

### 9.1 Review Cadence

| Review Type | Frequency | Owner | Participants | Output |
|-------------|-----------|-------|-------------|--------|
| Policy review | Quarterly | CTO | All policy signatories | Updated policy version |
| HITL effectiveness | Monthly | CTO + CCO | Agent owners, ML Engineering | Metrics report, improvement recommendations |
| Threshold calibration | Monthly | CPO + CFO + CSO | Demand Planning, Finance | Adjusted threshold values |
| SoD review | Annually | CCO | Internal Audit, External Auditor | Compliance certification |
| Full policy audit | Annually | External Auditor | All stakeholders | Audit report, control attestation |

### 9.2 Version Control

| Version | Date | Author | Changes | Approval |
| 1.0 | 2026-05-21 | CTO | Initial policy | Pending |
| 1.1 | 2026-05-21 | CTO | Post-review fixes: SLA alignment for 10 P1 scenarios, P0-Critical priority added, Agent-05/Agent-06 scenarios (H-043—H-047), conflict→HITL mapping table, sign-off accountability declarations | Pending |

### 9.3 Related Documents

| Document | Location | Relationship |
|----------|----------|-------------|
| Autonomy Levels Framework | `governance/autonomy-levels.md` | Defines L1/L2/L3 tiers referenced in this policy |
| Conflict Resolution Rules | `governance/conflict-resolution.md` | Arbitration flow when agents disagree |
| Agent Responsibility Matrix | `02-agent-responsibility-matrix.md` | Per-agent escalation paths and fallback behaviors |
| Security Architecture | `security/zero-trust-architecture.md` | RBAC, mTLS, and access control implementation |
| Compliance Automation | `security/compliance-automation.md` | SOX controls and regulatory mapping |
| Risk Register | `05-risk-register.md` | Risk scenarios that HITL gates are designed to mitigate |
| End-to-End Workflow | `06-end-to-end-workflow.md` | Worked example showing HITL in action during price spike |
| Implementation Roadmap | `04-implementation-roadmap.md` | Phase-dependent autonomy assignments |

---

## 10. Sign-Off

This policy requires sign-off from the following stakeholders. By signing, each stakeholder confirms:

- They have reviewed and understand the policy
- They accept the defined authorities and responsibilities
- They commit to SLA compliance within their domain
- They will ensure adequate coverage (backup approvers) during absences

| Role | Name | Signature | Date | Accountability Declaration |
|------|------|-----------|------|---------------------------|
| **Chief Technology Officer** | | | | Policy Owner. I certify this policy reflects the system architecture and commit to enforcing it across all agent deployments. I will ensure the HITL implementation supports all 9 agents and all 47 scenarios defined herein. |
| **Chief Financial Officer** | | | | Financial controls signatory. I accept designation as the financial decision approver (Section 3.1) and will maintain deputy coverage during absences. I will ensure compliance with SOX controls and deterministic financial rules. |
| **Chief Operations Officer** | | | | Production operations signatory. I accept designation as production/inventory decision approver and will ensure OEE, quality, and safety HITL gates are respected before any schedule override. |
| **Chief Procurement Officer** | | | | Procurement signatory. I accept designation as procurement decision approver and will maintain 24/7 coverage for P1-Priority procurement HITL tickets. |
| **Chief Sales Officer** | | | | Sales and pricing signatory. I accept designation as pricing/customer allocation approver and will ensure pricing changes >5% always receive HITL review before execution. |
| **Chief Risk Officer / CCO** | | | | Compliance and risk signatory. I confirm Agent-08 operates independently of execution agents. I will enforce compliance-first rule (C-06) without exception. |
| **Legal Counsel** | | | | Legal and regulatory signatory. I will review Agent-05 autonomy upgrades before activation (R-19) and approve all material contract term deviations. |
| **Chief Executive Officer** | | | | Final authority and escalation endpoint. I confirm this policy aligns with enterprise risk appetite and commit to supporting its enforcement across all business units. |
| **Head of Internal Audit** | | | | Policy compliance verification. I will conduct quarterly audits of HITL effectiveness, SLA compliance, and audit trail completeness, reporting findings to the Board Audit Committee. |

---

## Appendix A: HITL Ticket Example

```
┌─────────────────────────────────────────────────────────────────────┐
│  ╔═══════════════════════════════════════════════════════════════╗  │
│  ║                    HITL TICKET #H-2026-0042                  ║  │
│  ║                    CREATED: 2026-05-21T14:30:00Z             ║  │
│  ╚═══════════════════════════════════════════════════════════════╝  │
│                                                                     │
│  DECISION: Price Spike >10% — Material Buy/Hedge Decision           │
│  TRIGGER:  Copper C11000 spot price +20.2% in 2 hours               │
│  PRIORITY: P1-High                                    SLA: 1 hour  │
│  APPROVER: CFO + CPO (Joint Approval Required)                      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  BUSINESS IMPACT                                            │   │
│  │  • Monthly cost increase: $245K (at current consumption)     │   │
│  │  • Margin impact: -1.2% gross (-$98K EBITDA/month)           │   │
│  │  • Affected lines: Product A (38%→32.4%), B (22%→14.8%)     │   │
│  │  • Cash flow: +$245K monthly outflow                         │   │
│  │  • Inventory cover: 14 days at current consumption            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  AGENT RECOMMENDATION                                       │   │
│  │  ╔══════════════════════════════════════════════════════════╗│   │
│  │  ║ Option A: Hedge 60% at $9.12/kg forward                 ║│   │
│  │  ║  → $12K/month premium. Preserves margin                 ║│   │
│  │  ║  → Confidence: 0.85 (if strike resolves within 30d)     ║│   │
│  │  ║  → Data sources: LME, Bloomberg, S&P Global (3/3)       ║│   │
│  │  ║  → Model version: procurement-price-v2.3.1              ║│   │
│  │  ╚══════════════════════════════════════════════════════════╝│   │
│  │                                                             │   │
│  │  ALTERNATIVES:                                              │   │
│  │  • Option B: Pass through 50% cost (+10% price to customers) │   │
│  │    → -8% volume, margin +2.1% → HITL required (>5% change)  │   │
│  │  • Option C: Absorb cost (current autonomous path)           │   │
│  │    → -1.2% margin, volume flat → Approved within bounds      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  APPROVAL:  [Approve A]  [Approve B]  [Approve C]  [Custom]        │
│                                                                     │
│  ESCALATION:  Primary: CFO (15 min elapsed) → Secondary: CEO       │
│  ⏱ SLA Remaining: 45 minutes                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Appendix B: Responsibility Assignment Matrix (RAM)

```
┌─────────────────────────────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ Decision Area               │ CFO │ COO │ CPO │ CSO │ CCO │ CTO │ CEO │
├─────────────────────────────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│ Pricing >5%                 │  C  │     │     │  A  │  C  │     │  I  │
│ Pricing 2-5%                │  I  │     │     │  A  │     │     │     │
│ Production schedule >8h     │  I  │  A  │     │  C  │     │     │  I  │
│ Production schedule 2-8h    │     │  A  │     │     │     │     │     │
│ Supplier onboarding >$500K  │  C  │     │  A  │     │  C  │     │  I  │
│ Supplier onboarding <$500K  │     │     │  A  │     │     │     │     │
│ PO value >$500K             │  C  │     │  A  │     │     │     │  I  │
│ PO value $100K-$500K        │     │     │  A  │     │     │     │     │
│ Financial close adj >$50K   │  A  │     │     │     │  C  │     │  I  │
│ Financial close adj $10-50K │  A  │     │     │     │  C  │     │     │
│ Budget override >5%         │  A  │     │     │     │     │     │  C  │
│ Budget override 2-5%        │  A  │     │     │     │     │     │     │
│ Compliance violation (SOX)  │  I  │  I  │  I  │  I  │  A  │  I  │  C  │
│ Circuit breaker reset       │     │     │     │     │  C  │  A  │  I  │
│ Model deployment            │     │     │     │     │  C  │  A  │     │
│ Inventory realloc >$200K    │  C  │  A  │     │     │     │     │     │
│ Hedge activation            │  A  │     │  C  │     │     │     │  I  │
│ Emergency system halt       │  I  │  I  │  I  │  I  │  C  │  A  │  I  │
└─────────────────────────────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

Key: A = Approver  C = Consulted  I = Informed
```

## Appendix C: HITL Threshold Calibration Process

Thresholds in Section 4.1 should be reviewed and potentially recalibrated monthly based on:

1. **Override rate analysis**: If human approvers consistently override agent recommendations for a specific threshold, the threshold may be too tight or the agent model may need retraining
2. **False positive rate**: If HITL tickets are created but consistently approved without modification, the threshold may be too conservative
3. **Business environment changes**: Inflation, market volatility, or regulatory changes may require threshold adjustment
4. **ROI analysis**: Cost of HITL delays vs. cost of autonomous errors — recalibrate to optimize

**Calibration Formula**:
```
Optimal Threshold = Current Threshold × (Override Rate / Target Override Rate)

Example:
  Current threshold: PO value >$500K
  Override rate: 8% (target: 10-15%)
  → Threshold is too conservative → consider lowering to $400K
  → Wait: override rate is below target means humans agree with agent
  → Actually, keep threshold; increase autonomy instead
```

**Note**: Threshold changes of >20% require CFO approval. All threshold changes are logged and versioned.

---

*Document Version 1.0.0 | Next Review: 2026-08-21 | Policy Owner: CTO*
