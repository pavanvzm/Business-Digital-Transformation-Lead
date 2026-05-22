# 7. Evaluation Framework

> KPI definitions, model monitoring, cost-benefit analysis, audit schedule, success criteria

## 7.1 KPI Dashboard Framework

### KPI by Stakeholder

#### CFO Dashboard — Margin, Cost, Cash Flow

| KPI | Definition | Target | Threshold Warning | Update Freq | Source Agent |
|-----|-----------|--------|------------------|-------------|--------------|
| Gross Margin % | (Revenue - COGS) / Revenue | ≥35% | <32% | Real-time | Agent-07 |
| Operating Margin % | (EBIT) / Revenue | ≥15% | <12% | Daily | Agent-07 |
| COGS Variance % | \|Actual - Standard\| / Standard | <3% | >5% | Daily | Agent-07 |
| Cash Conversion Cycle | DIO + DSO - DPO | <45 days | >55 days | Weekly | Agent-07 |
| Free Cash Flow | Operating CF - CapEx | Positive | Negative 2mo | Monthly | Agent-07 |
| AI Compute Cost % | AI Cost / Margin Improvement | <0.5% | >0.7% | Weekly | Agent-09 |
| Budget Variance % | \|Actual - Budget\| / Budget | <5% | >8% | Monthly | Agent-07 |

#### COO Dashboard — OEE, Throughput, Quality

| KPI | Definition | Target | Threshold Warning | Update Freq | Source Agent |
|-----|-----------|--------|------------------|-------------|--------------|
| OEE % | Availability × Performance × Quality | >85% | <75% | Real-time | Agent-02 |
| Throughput | Units / production hour | Per line | -10% | Real-time | Agent-02 |
| First Pass Yield % | Good units / Total units | >97% | <95% | Real-time | Agent-02 |
| Schedule Adherence % | On-time starts | >95% | <90% | Daily | Agent-02 |
| MTBF | Hours between failures | >500h | <300h | Weekly | Agent-02 |
| MTTR | Hours to repair | <2h | >4h | Weekly | Agent-02 |
| Predictive Maintenance Accuracy | Correct predictions / Total | >85% | <75% | Weekly | Agent-02 |

#### CPO Dashboard — Forecast, Supplier, Inventory

| KPI | Definition | Target | Threshold Warning | Update Freq | Source Agent |
|-----|-----------|--------|------------------|-------------|--------------|
| Forecast Accuracy (MAPE) | Σ\|A-F\|/Σ\|A\| | <15% | >20% | Weekly | Agent-06 |
| Forecast Bias | Σ(A-F)/N | ±3% | ±5% | Weekly | Agent-06 |
| WAPE | Σ\|A-F\|/ΣA | <10% | >15% | Weekly | Agent-06 |
| Inventory Turnover | COGS / Avg Inventory | 6-8x | <4x or >10x | Monthly | Agent-03 |
| Stock-out Rate | Stock-out SKUs / Total SKUs | <1% | >3% | Daily | Agent-03 |
| Dead Stock % | 90d no-movement / Total | <3% | >5% | Monthly | Agent-03 |
| Supplier OTIF % | On-time, in-full | >95% | <90% | Weekly | Agent-01 |
| Supplier Risk Score | Composite (15 metrics) | <30/100 | >50/100 | Monthly | Agent-01 |

#### CSO Dashboard — Orders, Fulfillment, Revenue

| KPI | Definition | Target | Threshold Warning | Update Freq | Source Agent |
|-----|-----------|--------|------------------|-------------|--------------|
| Order Fulfillment Rate % | Orders shipped complete | >98% | <95% | Real-time | Agent-04 |
| On-Time Delivery % | Orders on-time | >95% | <90% | Daily | Agent-04 |
| Channel Margin % | Revenue - Channel cost | Per channel | -2% | Weekly | Agent-04 |
| Customer NPS | Survey-based | >50 | <30 | Monthly | Agent-05 |
| Returns Rate % | Returns / Shipments | <3% | >5% | Weekly | Agent-04 |
| Order Cycle Time | Order-to-delivery hours | <48h | >72h | Daily | Agent-04 |

#### CRO Dashboard — Risk, Compliance, Security

| KPI | Definition | Target | Threshold Warning | Update Freq | Source Agent |
|-----|-----------|--------|------------------|-------------|--------------|
| Risk Score (Operational) | Composite per process | <5/10 | >7/10 | Real-time | Agent-08 |
| Risk Score (Financial) | Composite per process | <4/10 | >6/10 | Real-time | Agent-08 |
| Compliance Violations | Count per month | 0 | ≥1 | Real-time | Agent-08 |
| Control Effectiveness | Automated control pass % | >98% | <95% | Monthly | Agent-08 |
| Audit Trail Completeness | Logs captured / expected | >99.9% | <99% | Daily | Agent-08 |
| Cybersecurity Score | CVSS-based | <4.0 | >6.0 | Real-time | Agent-08 |

#### CIO Dashboard — System Health

| KPI | Definition | Target | Threshold Warning | Update Freq | Source Agent |
|-----|-----------|--------|------------------|-------------|--------------|
| System Availability % | Uptime / Total | >99.9% | <99.5% | Real-time | Agent-09 |
| Critical Path Latency | 95th percentile | <2s | >5s | Real-time | Agent-09 |
| Agent Heartbeat | All agents healthy | 9/9 | <7/9 | Real-time | Agent-09 |
| Message Bus Lag | Unconsumed messages | <100 | >1000 | Real-time | Agent-09 |
| Model Drift % | Models with drift | <5% | >15% | Weekly | Agent-09 |
| Data Quality Score | Gates passed / total | >98% | <95% | Daily | Agent-09 |
| Human Intervention Rate | HITL overrides / Total | <10% | >20% | Weekly | Agent-09 |

## 7.2 Model Monitoring & Retraining

### Retraining Schedule

| Model | Retraining Frequency | Trigger (auto) | Data Window | Validation Holdout |
|-------|---------------------|----------------|-------------|-------------------|
| Demand Forecast (Prophet) | Monthly | MAPE >20% or drift detected | 2 years | 3 months |
| Demand Forecast (LightGBM) | Bi-weekly | MAPE >18% or drift detected | 1 year + features | 1 month |
| Ensemble Weights | Weekly | Ensemble MAPE > individual models | 3 months | 2 weeks |
| Price Optimization | Monthly | Margin degradation >2% | 6 months | 1 month |
| Vendor Scoring | Quarterly | Supplier OTIF drop >5% | 1 year | 1 quarter |
| Predictive Maintenance | Monthly | False positive rate >15% | 1 year | 3 months |
| Market Sentiment | Weekly | Sentiment vs actual correlation <0.5 | 3 months | 2 weeks |
| Anomaly Detection | Bi-weekly | False positive rate >10% | 6 months | 1 month |

### Model Drift Detection (Evidently AI)

```
┌────────────────────────────────────────────────────────────────────┐
│                    DRIFT DETECTION PIPELINE                         │
│                                                                    │
│  Production Model     ────▶  Feature Store (Redis)                 │
│       │                          │                                 │
│       │                          ▼                                 │
│       │              ┌────────────────────────────┐                │
│       │              │  Evidently AI Drift Report  │               │
│       │              │  • Data Drift (KS-test)     │               │
│       │              │  • Target Drift (PSI)       │               │
│       │              │  • Model Performance        │               │
│       │              │  • Data Quality             │               │
│       │              └────────────┬───────────────┘                │
│       │                           │                                │
│       │          ┌────────────────▼───────────────┐                │
│       │          │  Drift Severity Assessment      │               │
│       │          │  Low (<0.1) → Log only          │               │
│       │          │  Medium (0.1-0.2) → Alert +     │               │
│       │          │    schedule retraining           │               │
│       │          │  High (>0.2) → Alert + halt     │               │
│       │          │    autonomous → HITL + rollback  │               │
│       │          └────────────────────────────────┘                │
│       │                           │                                │
│       │                           ▼                                │
│       │              ┌────────────────────────────┐                │
│       └──────────────│  Decision:                  │               │
│                      │  • No action (drift <0.1)  │                │
│                      │  • Retrain (drift 0.1-0.2) │                │
│                      │  • Rollback + HITL (>0.2)  │                │
│                      └────────────────────────────┘                │
└────────────────────────────────────────────────────────────────────┘
```

## 7.3 Cost-Benefit Analysis Framework

### Tracking Model

```
┌────────────────────────────────────────────────────────────────────┐
│              COST-BENEFIT TRACKING (Monthly Review)                  │
│                                                                     │
│  BENEFITS (Monthly):                                                │
│  ├── Inventory reduction: $Value = (Baseline - Current) × Carrying% │
│  ├── Forecast accuracy improvement: $Value = (Rush orders avoided   │
│  │   + Write-off reduction + Overstock avoidance)                   │
│  ├── OEE improvement: $Value = Additional output × Margin           │
│  ├── Margin expansion: $Value = (New margin - Baseline) × Revenue   │
│  ├── Labor efficiency: $Value = (FTE reduction × Avg salary)        │
│  └── Risk avoidance: $Value = (Insurance premium reduction + Loss   │
│       avoidance)                                                     │
│                                                                      │
│  COSTS (Monthly):                                                    │
│  ├── Infrastructure: K8s, Kafka, storage, DBs                       │
│  ├── AI Compute: LLM API costs + ML training compute                │
│  ├── Engineering: Team salaries allocated                            │
│  ├── External APIs: Market data, news, scraping                     │
│  └── Depreciation: Phase investment / 36 months                     │
│                                                                      │
│  NET BENEFIT = Total Benefits - Total Costs                          │
│  ROI % = (Net Benefit / Total Costs) × 100                           │
│  Payback = Total Investment / Monthly Net Benefit                    │
└────────────────────────────────────────────────────────────────────┘
```

### Report Template

```json
{
  "period": "2026-05",
  "phase": "Phase 2 — Semi-Autonomous",
  "benefits": {
    "inventory_reduction": 420000,
    "forecast_accuracy": 185000,
    "oee_improvement": 95000,
    "margin_expansion": 380000,
    "labor_efficiency": 120000,
    "risk_avoidance": 50000,
    "total_benefits": 1250000
  },
  "costs": {
    "infrastructure": 85000,
    "ai_compute": 42000,
    "engineering": 310000,
    "external_apis": 18000,
    "depreciation": 95000,
    "total_costs": 550000
  },
  "net_benefit": 700000,
  "roi_percent": 127,
  "cumulative_payback_months": 4.2,
  "ai_compute_percent_of_margin": 0.38,
  "trend": {
    "net_benefit_3mo": [580000, 640000, 700000],
    "trend_direction": "improving"
  }
}
```

## 7.4 Audit Schedule

### Regular Audits

| Audit Type | Frequency | Scope | Owner | Deliverable |
|------------|-----------|-------|-------|-------------|
| Model Performance Review | Monthly | All production models: accuracy, drift, retraining status | ML Engineering | Model health report |
| Data Quality Audit | Monthly | Data quality gate pass rates, schema conformance | Data Engineering | Data quality scorecard |
| SOX Control Test | Quarterly | 47 SOX automated controls, segregation of duties | Compliance Officer | SOX control report |
| ISO 27001 Review | Quarterly | Information security controls, incident response, BCP | CISO | ISO readiness assessment |
| Cost-Benefit Analysis | Monthly | ROI tracking, cost allocation, benefit realization | CFO | Cost-benefit report |
| Agent Accuracy Decay | Weekly | Per-agent recommendation accuracy vs. actual outcomes | ML Engineering | Agent accuracy dashboard |
| Human Feedback Review | Bi-weekly | HITL decision patterns, override reasons, improvement opportunities | Product Owner | Feedback analysis |
| Security Penetration Test | Quarterly | Agent API, message bus, data lake, dashboard | Security | Pen test report |
| Full System Audit | Annually | Complete architecture, governance, compliance, security review | External Auditor | Audit report |

### Automated Continuous Controls

```
┌────────────────────────────────────────────────────────────────────┐
│                    CONTINUOUS CONTROL MONITORING                     │
│                                                                      │
│  Every Transaction (real-time):                                      │
│  • Segregation of duties: no single agent creates + approves         │
│  • Financial double-entry: every debit has matching credit           │
│  • Data lineage: every data point traced to source                   │
│  • Audit log: every action recorded (who, what, when, why, before,  │
│    after, confidence, alternatives)                                  │
│                                                                      │
│  Every Hour:                                                         │
│  • Agent health check: heartbeat, latency, error rate               │
│  • Message bus health: lag, throughput, dead-letter queue size      │
│  • Data freshness: last successful data quality gate                 │
│                                                                      │
│  Every Day:                                                          │
│  • KPI threshold check: all KPIs within bounds                      │
│  • Dual-write reconciliation: MAS vs legacy (Phase 1-2)             │
│  • Data quality: complete pass of all gates                         │
│                                                                      │
│  Every Week:                                                         │
│  • Model drift check: all production models                         │
│  • Forecast accuracy: MAPE/WAPE/bias by SKU                         │
│  • Cost tracking: AI compute cost vs. margin improvement             │
│  • Agent accuracy: recommendation accuracy vs. outcomes             │
└────────────────────────────────────────────────────────────────────┘
```

## 7.5 Success Criteria Verification

| Criterion | Baseline | 6-Month Target | 12-Month Target | Measurement Method | Verifying Phase |
|-----------|----------|----------------|-----------------|-------------------|----------------|
| Forecast error (MAPE) | Current baseline | <18% (20% reduction) | <15% | Weekly accuracy report | Phase 1-2 |
| Inventory turnover | Current ratio | +5% | +15% | Monthly inventory report | Phase 2-3 |
| Gross margin | Current % | +1-2% | +5-8% | Monthly P&L by product line | Phase 2-3 |
| Order fulfillment rate | Current % | >96% | >98% | Daily fulfillment report | Phase 2-3 |
| OEE | Current % | >80% | >85% | Real-time OEE dashboard | Phase 2-3 |
| MTTR from agent failure | N/A | <4 hours | <2 hours | Incident tracking system | Phase 2-3 |
| Human intervention rate | 100% (manual) | <20% | <10% | HITL tracking dashboard | Phase 2-3 |
| SOX/ISO audit readiness | Manual | Documented controls | Full automation | Internal audit prep | Phase 2-3 |
| AI compute cost (% of profit) | N/A | <1.0% | <0.5% | Monthly cost report | All phases |
| Data quality pass rate | N/A | >95% | >99% | Data quality dashboard | Phase 2-3 |

## 7.6 Disaster Recovery & Business Continuity

### RTO/RPO by Failure Scenario

| Scenario | RTO (Recovery Time) | RPO (Recovery Point) | Strategy |
|----------|---------------------|----------------------|----------|
| **Single agent failure** | <2 hours | Zero (event replay) | K8s pod restart, Kafka consumer rebalance |
| **Kafka cluster failure** | <30 minutes | <5 seconds | Active-passive broker replicas in same region |
| **PostgreSQL primary failure** | <15 minutes | <1 second (WAL streaming) | Patroni HA with automated failover to standby |
| **Data center outage** | <4 hours | <15 minutes | Cross-region active-passive DR; Kafka MirrorMaker |
| **Regional disaster** | <24 hours | <1 hour | Cold standby in second region; data from WORM backups |
| **LLM API provider outage** | <5 minutes | Zero | LiteLLM auto-failover to alternate provider or local quantized model |
| **Cyber attack / ransomware** | <48 hours (clean restore) | <24 hours | Immutable backups, WORM audit logs, offline restore |

### Business Continuity Testing

| Test Type | Frequency | Scope | Success Criteria |
|-----------|-----------|-------|-----------------|
| **Agent failover** | Weekly | Kill random agent pod → verify failover | <2-min autofail, zero data loss |
| **Kafka broker failover** | Monthly | Take down 1 broker → verify cluster health | <30s leader re-election, no data loss |
| **Database failover** | Monthly | Promote standby → verify read/write | <15s failover, no data corruption |
| **Full DR drill** | Quarterly | Shift all traffic to secondary region | RTO <4h, RPO <15min |
| **Chaos engineering** | Monthly | Inject latency, partition network, throttle CPU | System degrades gracefully, no data loss |

## 7.7 Capacity Planning Metrics

| Resource | Current Baseline | Growth Rate | Scaling Trigger | Max Capacity |
|----------|-----------------|-------------|-----------------|-------------|
| **Kafka throughput** | 50K msg/min | +15% quarterly | >70% broker CPU → add partition | 500K msg/min per cluster |
| **Data lake storage** | 5 TB | +20% quarterly | >80% capacity → add MinIO nodes | 500 TB per cluster |
| **PostgreSQL storage** | 200 GB | +10% quarterly | >70% → archive old partitions | 5 TB per instance |
| **Redis memory** | 8 GB | +15% quarterly | >75% → add shard | 64 GB per cluster |
| **Agent compute (CPU)** | 12 vCPU avg | +20% quarterly | >70% → scale HPA | 100 vCPU per namespace |
| **Agent compute (GPU)** | Not required | N/A | Forecast latency >2s → evaluate GPU | N/A |
| **LLM API calls** | 100K/month | +25% quarterly | Cost >0.5% margin → downgrade tier | Budget-capped |
| **IoT data ingestion** | 100 MB/day | +30% quarterly | >80% Kafka partition throughput | 2 GB/day per cluster |

### Data Lifecycle & Retention

| Layer | Active (Hot) | Warm | Cold (Archive) | Deletion |
|-------|-------------|------|----------------|----------|
| **Bronze (raw)** | 7 days | 30 days (compressed) | 90 days (Parquet, cost-optimized) | After 90 days |
| **Silver (cleaned)** | 90 days | 1 year | 3 years (Parquet) | After 3 years |
| **Gold (aggregated)** | 1 year | 3 years | 7 years (final snapshots) | After 7 years |
| **WORM audit logs** | — | — | 7 years (immutable, MinIO object lock) | Legal hold override only |
| **Model artifacts (MLflow)** | Current + 5 previous | All production versions | All versions (S3/Parquet) | Retain indefinitely |
| **Forecast outputs** | Current month | 2 years | 5 years | After 5 years |

## 7.8 Phase Gate Review Criteria

### Phase 1 → Phase 2 Gate

```
Gate Criteria Checklist:
□ Forecast MAPE <18% for pilot product line (4 consecutive weeks)
□ Data quality pass rate >90% across all sources
□ Dual-write reconciliation >95% match rate
□ System latency <5s for critical path
□ All 9 agents scaffolded and running (at least advisory mode)
□ HITL gate framework designed and approved
□ Security baseline controls implemented (mTLS, Vault, RBAC)
□ Phase 1 ROI validated ($200K+ inventory savings)
□ CPO, COO, and CTO sign-off obtained
→ Go/No-Go Decision: ________
```

### Phase 2 → Phase 3 Gate

```
Gate Criteria Checklist:
□ Forecast MAPE <15% for 3 product lines (8 consecutive weeks)
□ Data quality pass rate >95%
□ Dual-write reconciliation >99% match rate
□ System latency <2s for critical path
□ Human intervention rate <20% for L2 agents
□ HITL gates operational and tested (>100 approval flows)
□ SOX/ISO controls automated and verified
□ Phase 2 ROI validated ($3M+ annualized benefit)
□ Board-level sign-off for autonomous operations
→ Go/No-Go Decision: ________
```

---

*See also: [Implementation Roadmap](./04-implementation-roadmap.md) | [Risk Register](./05-risk-register.md)*
