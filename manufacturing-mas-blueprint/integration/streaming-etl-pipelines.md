# Integration: Streaming & ETL Pipelines

> Apache Kafka streaming, Apache Airflow + dbt batch processing, and pipeline orchestration

## Streaming Topology

```
┌────────────────────────────────────────────────────────────────────┐
│                    KAFKA STREAMING TOPOLOGY                          │
│                                                                      │
│  SOURCE TOPICS (External → Kafka)                                   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ erp.sap.*          — ERP events via Kafka Connect             │   │
│  │ mes.telemetry      — Machine sensor data (10Hz)               │   │
│  │ mes.quality        — QC results                               │   │
│  │ wms.inventory      — Inventory movements                      │   │
│  │ crm.orders         — Customer orders                          │   │
│  │ market.prices      — Commodity/competitor prices              │   │
│  │ market.news        — Industry news feeds                      │   │
│  │ banking.transactions— Payment/cash flow data                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                        │
│                              ▼                                        │
│  STREAM PROCESSING (Flink / ksqlDB)                                  │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ • Machine telemetry → OEE calculation (1-min windows)         │   │
│  │ • Price monitoring → threshold breach alerts                 │   │
│  │ • Inventory movements → stock level updates                  │   │
│  │ • Order flow → fulfillment prioritization                    │   │
│  │ • Quality results → SPC violation detection                  │   │
│  │ • Sentiment → trend alerts (5-min windows)                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                        │
│                              ▼                                        │
│  AGENT EVENT TOPICS (Kafka → Agents)                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ events.procurement     — Agent-01                            │   │
│  │ events.production      — Agent-02                            │   │
│  │ events.inventory       — Agent-03                            │   │
│  │ events.sales           — Agent-04                            │   │
│  │ events.market          — Agent-05                            │   │
│  │ events.forecast        — Agent-06                            │   │
│  │ events.finance         — Agent-07                            │   │
│  │ events.compliance      — Agent-08                            │   │
│  │ events.orchestrator    — Agent-09                            │   │
│  │ events.dead-letter     — Failed messages                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

## Key Stream Processing Jobs

| Job | Source Topic | Sink Topic | Window | Logic | SLAs |
|-----|-------------|------------|--------|-------|------|
| **OEE Calculation** | `mes.telemetry` | `events.production` | 1-min tumbling | Running time / Planned time × Performance × Quality | <5s latency |
| **Price Threshold Alert** | `market.prices` | `events.market`, `events.procurement` | None (per-event) | Compare vs. trailing 20-day moving average | <1s latency |
| **Inventory Level** | `wms.inventory` | `events.inventory` | None (per-event) | Maintain projected stock-out date | <2s latency |
| **Quality SPC** | `mes.quality` | `events.production` | 1-hour tumbling | Western Electric rules on last 25 samples | <30s latency |
| **Sentiment Trend** | `market.sentiment` | `events.market` | 5-min tumbling | 3-period moving average vs. baseline | <1min latency |

## Batch ETL Schedule (Airflow + dbt)

```
┌────────────────────────────────────────────────────────────────────┐
│                     AIRFLOW DAG SCHEDULE                            │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  DAG: bronze_to_silver (Hourly)                            │     │
│  │  ├── validate_schema  (Great Expectations)                  │     │
│  │  ├── deduplicate_data                                      │     │
│  │  ├── clean_transformations (dbt)                           │     │
│  │  └── data_quality_gate (Deequ)                             │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  DAG: silver_to_gold (Daily at 01:00)                     │     │
│  │  ├── aggregate_daily_kpis (dbt)                           │     │
│  │  ├── run_agent_ingestion_queries                          │     │
│  │  ├── update_feature_store (Redis)                         │     │
│  │  └── reconcile_dual_write                                 │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  DAG: model_training (Weekly on Sunday 02:00)             │     │
│  │  ├── fetch_training_data (Delta → feature store)          │     │
│  │  ├── train_models (Prophet, LightGBM, SARIMA)             │     │
│  │  ├── validate_on_holdout (MAPE, WAPE, Bias)               │     │
│  │  ├── ensemble_weight_optimization                         │     │
│  │  ├── register_models (MLflow)                             │     │
│  │  └── deploy_if_improved (>5% accuracy gain)               │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  DAG: financial_close (Monthly Day 1)                     │     │
│  │  ├── validate_cost_data (Agent-07)                        │     │
│  │  ├── run_cogs_calculations (deterministic)                │     │
│  │  ├── generate_pnl (rule-based)                            │     │
│  │  ├── run_sox_controls (47 automated checks)               │     │
│  │  ├── generate_financial_statements                        │     │
│  │  └── notify_finance_team_for_review                       │     │
│  └────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────┘
```

## Data Lineage (OpenLineage)

```
Every data transformation is traced via OpenLineage:

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Bronze     │────▶│  Silver     │────▶│  Gold       │
│  Table      │     │  Table      │     │  View       │
│             │     │             │     │             │
│ Dataset:    │     │ Dataset:    │     │ Dataset:    │
│ ...         │     │ ...         │     │ ...         │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Marquez    │
                    │  Lineage    │
                    │  Dashboard  │
                    └─────────────┘

Lineage captured for:
- Input datasets (with version)
- Output datasets (with version)
- Transformation logic (dbt model / Flink job)
- Run ID, timestamps, duration
- Input/output row counts
- Data quality check results
```
