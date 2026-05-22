# Governance: Conflict Resolution Rules

> Cross-agent conflict detection, arbitration, and priority routing

## Conflict Types & Resolution Matrix

| ID | Conflict Pattern | Detection | Resolution | Escalation |
|----|-----------------|-----------|------------|------------|
| C-01 | Inventory Agent recommends reduction BUT Sales Agent forecasts demand spike | Agent-03 stock-out risk vs. Agent-06 forecast increase | Orchestrator runs cost-benefit: cost of stock-out vs. cost of holding | HITL if gap >$100K impact |
| C-02 | Procurement wants alternative supplier BUT Financial flags higher cost | Agent-01 alt vendor cost vs. Agent-07 margin impact | Cost-benefit analysis: total cost of ownership (incl. switching, quality risk) | HITL if cost gap >5% |
| C-03 | Production wants schedule change BUT Sales disagrees (committed orders) | Agent-02 schedule vs. Agent-04 customer commitments | Validate against firm orders; if affected → HITL; if forecast → negotiate | HITL if any committed order affected |
| C-04 | Forecast demand drops BUT Procurement already placed orders | Agent-06 revised forecast vs. Agent-01 PO status | Root cause → adjust reorder point; expedite, cancel, or defer | HITL if PO value >$250K |
| C-05 | Market Intelligence signals price war BUT Sales wants to hold price | Agent-05 competitor pricing vs. Agent-04 pricing recommendation | Elasticity analysis: volume loss vs. margin loss at current price | HITL if margin impact >2% |
| C-06 | Compliance flags violation BUT Operations wants to continue | Agent-08 compliance alert vs. Agent-02 production | IMMEDIATE HALT → HITL mandatory; compliance always wins | CCO final authority |
| C-07 | Financial shows negative margin BUT Sales insists on fulfilling order | Agent-07 margin calc vs. Agent-04 fulfillment commitment | Validate cost accuracy; if negative margin confirmed → HITL to decide | CFO final authority |
| C-08 | Predictive recommends build inventory BUT Finance wants cash conservation | Agent-06 demand confidence vs. Agent-07 cash flow forecast | Risk assessment: stock-out cost vs. borrowing cost | HITL if >$500K cash impact |

## Arbitration Flow

```
┌────────────────────────────────────────────┐
│           CONFLICT DETECTED                 │
│  (Orchestrator receives conflicting events) │
└──────────────────┬─────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────┐
│         CONFLICT CLASSIFICATION             │
│  • Type: C-01 through C-08                  │
│  • Severity: Low / Medium / High / Critical │
│  • Impact: $ estimate                        │
└──────────────────┬─────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────┐
│         AUTO-RESOLUTION ATTEMPT             │
│  • Run cost-benefit analysis                │
│  • Check conflict resolution rule           │
│  • Determine if HITL required               │
└──────────────────┬─────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌─────────────────┐  ┌─────────────────────────┐
│ AUTO-RESOLVED    │  │  HITL REQUIRED           │
│ • Resolution     │  │ • Create HITL ticket     │
│   published      │  │ • Present both sides     │
│ • Agents         │  │ • Include impact         │
│   notified       │  │ • Recommend resolution   │
│ • Audit logged   │  │ • SLA: based on severity │
└─────────────────┘  └─────────────────────────┘
```

## Priority Routing

| Priority | Definition | Routing Rule | Examples |
|----------|-----------|-------------|----------|
| P0-Critical | Immediate safety/compliance risk | Route to CTO/CCO within 5 min; SMS + call | Compliance violation, safety hazard |
| P1-High | Significant financial/operational impact | Route to VP within 15 min; Slack + email | Pricing >5%, production stop, KPI breach |
| P2-Medium | Moderate impact, needs human judgment | Route to Manager within 2 hours; task queue | Supplier choice, inventory allocation |
| P3-Low | Minor optimization trade-off | Route to Analyst within 24 hours; email digest | Cost vs. service level fine-tuning |
