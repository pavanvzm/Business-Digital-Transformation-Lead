# Governance: Human-in-the-Loop (HITL) Gates

> Mandatory human approval scenarios, SLA matrix, and escalation protocols

## Mandatory HITL Scenarios

| Scenario | Trigger | Approver | SLA | Fallback if Unanswered |
|----------|---------|----------|-----|------------------------|
| **Pricing change >5%** | Agent-04 pricing recommendation | CSO / Pricing Committee | 1 hour | Auto-escalate to CEO; if no response in 4h → no change |
| **Production schedule override** | Agent-02 schedule change >8h | Production Manager | 2 hours | Use conservative default schedule |
| **Supplier onboarding** | New vendor >$500K annual value | CPO / Sourcing Director | 24 hours | Delay onboarding; use existing suppliers |
| **Financial closing adjustment** | Agent-07 identifies >$50K variance | CFO / Controller | 4 hours | Flag and carry forward; close with note |
| **Compliance-critical decision** | Agent-08 flags SOX/regulatory violation | CCO / Legal Counsel | 1 hour | HALT all related processes until resolved |
| **Budget override >5%** | Agent-07 detects budget variance | CFO | 24 hours | Flag variance; no action until approved |
| **Model deployment to production** | MLflow model accuracy validation | ML Engineering Lead | 48 hours | Keep previous model; deploy on approval |
| **Circuit breaker reset** | Agent-09 detects recovery | CTO / System Architect | 2 hours | Maintain advisory mode until reset |

## HITL Ticket Lifecycle

```
┌────────────────────────────────────────────────────────────┐
│                  HITL TICKET LIFECYCLE                      │
│                                                             │
│  1. CREATED                                                 │
│     • Trigger condition met                                 │
│     • Orchestrator generates ticket #H-XXXX                │
│     • Full context attached: before/after, impact, options  │
│                                                             │
│  2. NOTIFIED                                                │
│     • Approver alerted via configured channel               │
│       (Dashboard, Slack/Teams, Email, SMS)                  │
│     • SLA timer starts                                      │
│     • Escalation chain pre-configured:                      │
│       Primary → Secondary → Tertiary                        │
│                                                             │
│  3. REVIEW                                                  │
│     • Approver reviews context + agent recommendations      │
│     • View alternatives considered                          │
│     • Check business impact estimation                      │
│     • Can request additional analysis from agent            │
│                                                             │
│  4. DECISION                                                │
│     • Approve: Execute as recommended                      │
│     • Deny: Return with reason, no action taken             │
│     • Modify: Provide parameters, agent re-executes         │
│     • Escalate: Route to higher authority                   │
│                                                             │
│  5. CLOSED                                                  │
│     • Decision logged to immutable audit trail              │
│     • Agent receives result and continues                   │
│     • HITL database updated for trend analysis              │
│     • Feedback loop: model retraining if override pattern   │
└────────────────────────────────────────────────────────────┘
```

## HITL Notification Channels

| Channel | Priority Level | Format | Retry Policy |
|---------|---------------|--------|-------------|
| **Dashboard** | All levels | Interactive panel with accept/deny/modify | N/A — persistent |
| **Slack/Teams** | P1-Critical, P2-High | Rich card with decision buttons | 3 retries (5 min apart) |
| **Email** | P3-Medium, P4-Low | Summary with link to dashboard | 2 retries (1 hour apart) |
| **SMS/Call** | P1-Critical only | Alert with ticket ID | Call once, SMS every 5 min × 3 |
