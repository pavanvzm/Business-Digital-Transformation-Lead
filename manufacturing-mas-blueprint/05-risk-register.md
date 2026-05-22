# 5. Risk Register & Mitigation

> Comprehensive risk identification, assessment, ownership, and mitigation strategies

## 5.1 Risk Matrix Overview

| ID | Risk Category | Risk Description | Likelihood | Impact | Risk Score | Owner | Phase |
|----|--------------|-----------------|-----------|--------|-----------|-------|-------|
| R-01 | Data | Data quality failures (missing, stale, incorrect data ingested) | High (3) | Critical (4) | **12** | Data Engineering Lead | All |
| R-02 | AI/ML | Model hallucination or inaccurate forecasts driving wrong decisions | Medium (2) | Critical (4) | **8** | ML Engineering Lead | All |
| R-03 | AI/ML | Concept/model drift degrades forecast accuracy over time | High (3) | High (3) | **9** | ML Engineering Lead | 2+ |
| R-04 | Technical | Kafka/Pulsar cluster failure or message loss | Low (2) | Critical (4) | **8** | Platform Engineering | All |
| R-05 | Technical | API rate limiting or disconnection from ERP/MES | Medium (3) | High (3) | **9** | Integration Lead | All |
| R-06 | Vendor | Vendor lock-in to LLM provider or cloud service | Medium (2) | High (3) | **6** | CTO | All |
| R-07 | Operational | Production disruption caused by agent error or misconfiguration | Medium (2) | Critical (4) | **8** | COO | 2+ |
| R-08 | Operational | Agent conflict causes contradictory actions (e.g., buy more but forecast less) | Medium (2) | High (3) | **6** | Orchestrator Lead | 2+ |
| R-09 | Security | Data breach via agent API or messaging layer | Low (2) | Critical (4) | **8** | CISO | All |
| R-10 | Security | Unauthorized agent action due to RBAC misconfiguration | Low (2) | Critical (4) | **8** | Security Engineer | All |
| R-11 | Compliance | SOX/ISO audit failure due to insufficient system controls | Medium (2) | Critical (4) | **8** | Compliance Officer | 2+ |
| R-12 | Compliance | GDPR/CCPA violation via automated data processing | Medium (2) | Critical (4) | **8** | DPO | All |
| R-13 | Financial | AI-proposed pricing violates antitrust/price-fixing regulations | Low (1) | Critical (4) | **4** | Legal Counsel | 2+ |
| R-14 | Operational | Low-connectivity fallback fails during network outage | Medium (2) | High (3) | **6** | Infrastructure Lead | 3 |
| R-15 | Operational | Legacy system incompatibility during dual-write migration | Medium (3) | Medium (2) | **6** | Integration Lead | 1-2 |
| R-16 | AI/ML | AI compute costs exceed 0.5% of marginal profit gain | Medium (2) | Medium (2) | **4** | CFO | All |
| R-17 | Operational | Insufficient human skills to operate/override the system | Medium (3) | Medium (2) | **6** | HR/CTO | 2+ |
| R-18 | Technical | Dead-letter queue overflow causing message loss | Low (2) | Medium (2) | **4** | Platform Engineering | All |
| R-19 | Legal | Market Intelligence Agent auto-trading signals violate antitrust/price-fixing regulations | Low (1) | Critical (4) | **4** | Legal Counsel | 3 |
| R-20 | Technical | Kafka vendor lock-in or critical failure with no migration path | Medium (2) | High (3) | **6** | Platform Engineering | All |
| R-21 | Operational | Rapid demand pattern shift (new product, market disruption) exceeds monthly retrain cadence | Medium (2) | High (3) | **6** | ML Engineering Lead | All |
| R-22 | Infrastructure | Data center outage causes complete system unavailability | Low (2) | Critical (4) | **8** | Infrastructure Lead | 2+ |

## 5.2 Detailed Risk Descriptions & Mitigations

---

### R-01: Data Quality Failures

**Description**: Missing fields, stale data, incorrect transformations, or schema drift in ingested data causing agents to make decisions on bad data.

**Trigger Conditions**: 
- Data quality gate failure rate >5% for 3 consecutive runs
- Schema validation errors in >1% of messages
- Agent confidence scores <0.6 due to data anomalies

**Mitigation**:
1. **Preventive**: Great Expectations automated data quality gates at every ingestion point (bronze → silver → gold)
2. **Detective**: Real-time data quality dashboard with alerting; automated data health scoring for every source
3. **Corrective**: 
   - Stale data: agent uses last-known-good data with confidence penalty
   - Schema drift: automated schema evolution detection + notification
   - Data quality failure: route to dead-letter queue → human review → reprocess
4. **Ownership**: Data Engineering Lead

**Fallback**: Agents operate on last-known-good data with explicit "data_stale" flag in messages; all decisions from stale data include confidence discount.

---

### R-02: Model Hallucination / Inaccurate Forecasting

**Description**: LLM or ML model produces plausible but incorrect forecasts, price predictions, or optimization recommendations.

**Trigger Conditions**:
- Forecast error (MAPE) exceeds 25% for 3 consecutive weekly evaluations
- Agent recommendation confidence score <0.7
- Human override rate >15% for a specific agent's suggestions

**Mitigation**:
1. **Preventive**: 
   - All LLM outputs include citations and confidence scores
   - Forecasting ensemble (Prophet + LightGBM + SARIMA) — never single model
   - RAG grounding: every forecast references historical data and market signals
2. **Detective**: 
   - Evidently AI drift detection on model inputs vs. training data
   - Confidence interval monitoring: actuals outside 95% CI triggers investigation
   - Automated backtesting against last 30 days of actuals
3. **Corrective**: 
   - Auto-rollback to last known-good model version (MLflow)
   - Trigger retraining pipeline with expanded data
   - Escalate to HITL if accuracy drop exceeds 5% in 7 days
4. **Ownership**: ML Engineering Lead

**Non-negotiable**: No black-box LLM decision for payroll, compliance filings, customer contracts, or safety-critical production steps.

---

### R-03: Concept / Model Drift

**Description**: Statistical properties of target variable change over time, degrading model accuracy. E.g., post-pandemic demand patterns differ from training data.

**Trigger Conditions**:
- Prediction drift (Evidently AI): distribution distance >0.2 (PSI)
- Data drift: feature distribution shift >0.25 (KS-test)
- Model accuracy decline >5% in any 7-day window
- Actuals outside predicted confidence interval >20% of the time

**Mitigation**:
1. **Preventive**: 
   - Monthly retraining cadence with latest data
   - Feature store with freshness monitoring
   - Regular seasonality re-calibration
2. **Detective**: 
   - Evidently AI drift dashboards per model
   - Automated drift alerts with severity levels
3. **Corrective**: 
   - Auto-retrain with expanded window
   - Rollback to last known-good model (MLflow)
   - HITL if drift not corrected within one retraining cycle
4. **Ownership**: ML Engineering Lead

---

### R-07: Production Disruption from Agent Error

**Description**: Agent-02 (Production) makes incorrect scheduling decision causing line stoppage, quality incident, or safety issue.

**Trigger Conditions**:
- Agent issues production override outside approved parameters
- Quality defect rate >5% following agent recommendation
- Safety system flags agent-commanded machine state

**Mitigation**:
1. **Preventive**: 
   - Agent-02 operates at L2 (Semi-Autonomous): all schedule changes >2h require HITL
   - Hard bounds on machine parameters (speed, temperature, pressure)
   - Safety-critical decisions always routed through MES safety interlock
2. **Detective**: 
   - Real-time OEE monitoring with automated alerts
   - Quality SPC (Statistical Process Control) violation detection
   - Agent-08 (Compliance) monitors all production commands
3. **Corrective**: 
   - Immediate HITL escalation + agent → advisory mode
   - Root cause analysis within 4 hours
   - Model retraining / rule update before returning to autonomous mode
4. **Ownership**: COO / VP Manufacturing

**Non-negotiable**: No autonomous decisions on safety-critical machine controls. MES safety interlock always overrides agent.

---

### R-09: Data Breach via Agent API/Messaging

**Description**: Unauthorized access to agent APIs, message bus, or data lake exposes sensitive business data (pricing, customer info, financials).

**Trigger Conditions**:
- SIEM detects unusual API call patterns
- Authentication failure rate >5% in 1 hour
- Unauthorized topic subscription attempt on Kafka

**Mitigation**:
1. **Preventive**: 
   - Zero-trust architecture: mTLS for all service-to-service communication
   - RBAC/ABAC with HashiCorp Vault for secrets
   - API Gateway (Kong) with rate limiting + OAuth2
   - AES-256 at rest, TLS 1.3 in transit
2. **Detective**: 
   - OpenTelemetry-based audit trail for every API call
   - SIEM integration (Splunk/ELK) with automated alerting
   - Kafka ACL audit — automated weekly review
3. **Corrective**: 
   - Automated credential rotation (Vault)
   - API key revocation within 5 minutes
   - Incident response playbook: isolate → investigate → remediate
4. **Ownership**: CISO

---

### R-11: SOX/ISO Audit Failure

**Description**: Insufficient audit trails, segregation of duties, or control evidence for SOX/ISO auditor review.

**Trigger Conditions**:
- Automated control test failure rate >2%
- Missing audit records for any financial posting
- Segregation of duty violation detected

**Mitigation**:
1. **Preventive**: 
   - SOX control automation: 47 automated checks before financial close
   - Immutable WORM audit logs for all agent actions
   - Segregation of duties enforced at architecture level (no single agent creates + approves)
2. **Detective**: 
   - Continuous control monitoring dashboard
   - Automated SOX deficiency reporting
   - Agent-08 compliance scoring
3. **Corrective**: 
   - Automated control re-test after remediation
   - Root cause analysis within 24 hours
   - HITL for any control failure affecting financial reporting
4. **Ownership**: Compliance Officer / Internal Audit

---

### R-16: AI Compute Costs Exceed Budget

**Description**: LLM inference costs exceed 0.5% of marginal profit improvement, eroding ROI.

**Trigger Conditions**:
- Monthly AI compute cost >0.5% of estimated margin improvement
- Cost per forecast >$0.50
- API cost growth >10% month-over-month

**Mitigation**:
1. **Preventive**: 
   - LiteLLM cost-based routing (cheaper models for non-critical tasks)
   - Response caching for repeated queries (Redis)
   - Model quantization (Int8/FP16) for local inference
   - Budget alerts at 70%, 85%, 100% of threshold
2. **Detective**: 
   - Weekly cost dashboard per agent per model
   - Cost-per-transaction tracking
3. **Corrective**: 
   - Auto-downgrade model tier when costs exceed threshold
   - Route to local quantized models as fallback
   - CFO-approval required for model upgrade
4. **Ownership**: CFO / CTO

---

### R-19: Auto-Trading Compliance Risk

**Description**: Agent-05 (Market Intelligence) L2 autonomy with auto-trading signals in Phase 3 could violate antitrust, price-fixing, or market manipulation regulations.

**Trigger Conditions**:
- Agent-05 generates price recommendation that matches competitor pricing within ±1%
- Auto-trading signal executed without legal review
- Regulator inquiry on pricing practices

**Mitigation**:
1. **Preventive**: Legal review gate before L2 activation; all pricing signals logged with full market context
2. **Detective**: Pattern matching against competitor pricing → flag for collusion risk
3. **Corrective**: Immediate halt of all pricing signals → manual review → legal sign-off
4. **Ownership**: Legal Counsel / CCO

**Non-negotiable**: Agent-05 remains L1 (Advisory) until legal team explicitly approves L2 parameters. No auto-execution of pricing signals without human approval.

---

### R-20: Kafka Lock-In / Failure

**Description**: Architecture is heavily dependent on Kafka for all inter-agent communication. No documented migration path to alternatives (Pulsar, NATS).

**Trigger Conditions**:
- Kafka licensing changes or becomes cost-prohibitive
- Critical Kafka vulnerability with no patch
- Performance degradation not resolvable within Kafka architecture

**Mitigation**:
1. **Preventive**: Abstract all messaging behind a common interface (CloudEvents); design for topic-exchange compatibility
2. **Detective**: Quarterly review of alternative message bus technologies
3. **Corrective**: Documented migration path to Pulsar (same pub/sub paradigm); maintain compatibility layer
4. **Ownership**: Platform Engineering Lead

---

### R-21: Rapid Demand Pattern Shift

**Description**: New product launch, market disruption, or black swan event causes demand patterns to shift faster than monthly retraining cadence.

**Trigger Conditions**:
- Forecast MAPE >30% for 3 consecutive days
- New product SKU with no historical data
- Demand distribution KS-test distance >0.3 vs. training data

**Mitigation**:
1. **Preventive**: Implement online learning (LightGBM incremental training) for rapid adaptation
2. **Detective**: Daily drift detection with auto-retrain trigger when MAPE >30%
3. **Corrective**: Trigger unscheduled retraining with expanded window (+6 months); if accuracy not restored in 2 cycles → HITL for manual override
4. **Ownership**: ML Engineering Lead

---

### R-22: Data Center Outage

**Description**: Complete loss of primary data center due to natural disaster, power failure, or cyber attack.

**Trigger Conditions**:
- Primary data center unavailability >5 minutes
- Critical infrastructure component failure (network, power, cooling)

**Mitigation**:
1. **Preventive**: Active-passive DR in secondary region; automated DNS failover
2. **Detective**: Synthetic transaction monitoring every 30s from multiple locations
3. **Corrective**: 
   - RTO: <4 hours for critical systems (Kafka, PostgreSQL, Delta Lake)
   - RPO: <15 minutes data loss (Kafka cross-region replication)
   - Failover: automated DNS switch, PostgreSQL WAL streaming to standby
4. **Ownership**: Infrastructure Lead / CTO

---

## 5.3 Escalation Matrix

| Severity | Definition | Response Time | Escalation Path |
|----------|-----------|--------------|-----------------|
| **Critical** | System down, data loss, compliance violation, safety incident | <15 minutes | Agent-08 → Orchestrator → CTO/CISO/CRO → CEO |
| **High** | KPI breach, model failure, significant forecast error | <1 hour | Agent → Orchestrator → Functional VP |
| **Medium** | Degraded performance, non-critical data quality issue | <4 hours | Agent → Orchestrator → Lead Engineer |
| **Low** | Minor anomaly, non-urgent model drift | <24 hours | Agent → Orchestrator → On-call engineer |

---

## 5.4 Incident Response Playbook

```
┌─────────────────────────────────────────────────────────────┐
│                    INCIDENT RESPONSE FLOW                     │
│                                                             │
│  Alert Triggered                                             │
│      │                                                       │
│      ▼                                                       │
│  Auto-diagnosis (Orchestrator)                               │
│      │                                                       │
│      ├── Known issue? → Auto-remediation (playbook)          │
│      │                                                       │
│      └── Unknown issue? → Incident #INC-XXXX created         │
│              │                                               │
│              ▼                                               │
│  Severity Classification (Critical/High/Medium/Low)          │
│              │                                               │
│              ▼                                               │
│  Assign Owner (on-call rotation)                             │
│              │                                               │
│              ▼                                               │
│  Investigation (full trace from OpenTelemetry + audit logs)  │
│              │                                               │
│              ▼                                               │
│  Remediation (rollback, model swap, HITL, config change)     │
│              │                                               │
│              ▼                                               │
│  Validation (re-test, dual-write confirm, KPI check)         │
│              │                                               │
│              ▼                                               │
│  Post-mortem (root cause, lesson, playbook update)            │
└─────────────────────────────────────────────────────────────┘
```

---

*See also: [Compliance Automation](../security/compliance-automation.md) | [Evaluation Framework](./07-evaluation-framework.md)*
