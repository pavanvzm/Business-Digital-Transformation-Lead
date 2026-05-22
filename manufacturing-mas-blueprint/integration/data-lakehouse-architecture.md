# Integration: Data Lakehouse Architecture

> Delta Lake + Apache Iceberg medallion architecture for manufacturing intelligence

## Medallion Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          LAKEHOUSE ARCHITECTURE                         │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  BRONZE LAYER (Raw Ingestion)                                    │  │
│  │                                                                   │  │
│  │  Tables:                                                         │  │
│  │  • bronze_erp_purchase_orders    — Raw PO data from SAP/Oracle   │  │
│  │  • bronze_erp_production_orders   — Raw production order data    │  │
│  │  • bronze_erp_financial_postings  — Raw GL journal entries       │  │
│  │  • bronze_mes_machine_telemetry   — Raw sensor data (10Hz)       │  │
│  │  • bronze_mes_quality_results     — Raw QC lab results           │  │
│  │  • bronze_crm_customer_orders     — Raw customer orders/EDI      │  │
│  │  • bronze_wms_inventory_snapshots — Raw inventory counts         │  │
│  │  • bronze_market_competitor_pricing— Raw scraped pricing data    │  │
│  │  • bronze_market_social_sentiment  — Raw social media mentions   │  │
│  │  • bronze_banking_cash_transactions— Raw bank feeds              │  │
│  │                                                                   │  │
│  │  Format: Append-only, partitioned by date/hour                   │  │
│  │  Retention: 7 days (active) → 90 days (cold storage)            │  │
│  │  Data Quality: Flag errors (don't filter)                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  SILVER LAYER (Cleaned & Enriched)                               │  │
│  │                                                                   │  │
│  │  Tables:                                                         │  │
│  │  • silver_dim_product          — Product master (SCD Type 2)     │  │
│  │  • silver_dim_vendor           — Vendor master with ESG scores   │  │
│  │  • silver_dim_customer         — Customer master with tier       │  │
│  │  • silver_dim_material         — Raw material catalog            │  │
│  │  • silver_dim_machine          — Machine master with specs       │  │
│  │  • silver_dim_calendar         — Fiscal calendar, holidays       │  │
│  │  • silver_fct_purchase_orders  — Cleaned PO with line items      │  │
│  │  • silver_fct_production       — Cleaned production runs         │  │
│  │  • silver_fct_inventory_movements— Cleaned inventory transactions │  │
│  │  • silver_fct_sales_orders     — Cleaned sales with product      │  │
│  │  • silver_fct_market_prices    — Deduplicated, validated prices  │  │
│  │  • silver_fct_quality_results  — Cleaned QC with pass/fail       │  │
│  │  • silver_fct_financial_entries — Cleaned GL entries             │  │
│  │                                                                   │  │
│  │  Format: Deduplicated, validated, cleansed                        │  │
│  │  Retention: 90 days (hot) → 1 year (warm)                       │  │
│  │  Data Quality: Great Expectations pass required                  │  │
│  │  Transform: dbt models with full documentation                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  GOLD LAYER (Business-Ready)                                     │  │
│  │                                                                   │  │
│  │  Tables:                                                         │  │
│  │  • gold_forecast_demand          — SKU-level demand forecast      │  │
│  │  • gold_forecast_accuracy        — Actual vs. forecast tracking  │  │
│  │  • gold_inventory_health         — Stock levels, turns, dead stock│  │
│  │  • gold_oee_daily                — OEE by line/day/shift         │  │
│  │  • gold_cogs_analysis            — COGS breakdown by product     │  │
│  │  • gold_margin_report            — Gross/net margin by SKU       │  │
│  │  • gold_cash_flow                — 13-week cash flow projection  │  │
│  │  • gold_procurement_performance  — Vendor scorecard metrics      │  │
│  │  • gold_sales_fulfillment        — Order fulfillment dashboard   │  │
│  │  • gold_risk_scores              — Operational/financial risk    │  │
│  │  • gold_compliance_controls      — SOX/ISO control status        │  │
│  │  • gold_agent_performance        — Agent accuracy/health metrics │  │
│  │  • gold_ai_compute_costs         — LLM inference costs tracking  │  │
│  │                                                                   │  │
│  │  Format: Aggregated, materialized views                           │  │
│  │  Retention: 1 year (hot) → 3 years (warm) → 7 years (archive)   │  │
│  │  Access: Agent-consumable API + Grafana dashboards               │  │
│  │  Update: Micro-batch (5 min) for operational, daily for analytics│  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  STORAGE: MinIO (S3-compatible, self-hosted, WORM for audit)           │
│  CATALOG: Apache Hive Metastore / Unity Catalog                        │
│  LINEAGE: OpenLineage → Marquez Dashboard                              │
│  VERSIONING: Delta Lake time travel + DVC for model data               │
└─────────────────────────────────────────────────────────────────────────┘
```

## Streaming & Batch Architecture

```
                         ┌─────────────────────┐
                         │   External Sources   │
                         │  ERP, MES, CRM, IoT  │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │     Kafka Connect / Pulsar    │
                    │     (Source Connectors)       │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │      Stream Processing         │
                    │  ┌─────────────────────────┐  │
                    │  │  Real-time (Flink):     │  │
                    │  │  • Machine telemetry    │  │
                    │  │  • OEE calculations     │  │
                    │  │  • Quality alerts       │  │
                    │  │  • Price monitoring     │  │
                    │  │  • Inventory movements  │  │
                    │  └─────────────────────────┘  │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │      Batch Processing          │
                    │  ┌─────────────────────────┐  │
                    │  │  Airflow DAGs → dbt:    │  │
                    │  │  • Hourly: Bronze→Silver │  │
                    │  │  • Daily: Silver→Gold   │  │
                    │  │  • Weekly: Retraining   │  │
                    │  │  • Monthly: Reporting   │  │
                    │  └─────────────────────────┘  │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │      Data Quality Gates       │
                    │  Great Expectations + Deequ   │
                    └───────────────────────────────┘
```

## Time-Series Architecture (InfluxDB)

```
Measurement: machine_telemetry
├── Tags: machine_id, line_id, plant_id, metric_type
├── Fields: value, unit, quality_flag
├── Timestamp: nanosecond precision
└── Retention: 
    ├── Raw (10s resolution): 7 days
    ├── Aggregated (1min): 30 days
    ├── Aggregated (1hour): 1 year
    └── Downsampled (1day): 5 years

Measurement: market_prices
├── Tags: commodity_code, exchange, currency
├── Fields: spot_price, futures_1m, futures_3m, volume, open_interest
└── Retention: 2 years (no downsampling — financial audit requirement)

Measurement: agent_metrics
├── Tags: agent_id, action_type, status
├── Fields: latency_ms, confidence_score, input_tokens, output_tokens
└── Retention: 90 days
```

## Data Quality Gates

| Gate | Stage | Checks | Action on Failure |
|------|-------|--------|-------------------|
| **Schema Validation** | Bronze → Silver | Column types, nullability, required fields | Reject batch, alert data engineering |
| **Freshness Check** | All stages | Max age of data (configurable per source) | Flag as stale, use last-good-data |
| **Referential Integrity** | Silver → Gold | Foreign key check (e.g., product_id exists in dim_product) | Reject orphaned records, alert |
| **Statistical Bounds** | Price, cost data | Value within 3σ of moving average | Flag as outlier, route to manual review |
| **Distribution Check** | Forecast actuals | Actual vs. predicted KS-test <0.2 | Drift alert → retraining trigger |
| **Uniqueness** | Deduplication | No duplicate primary keys | Deduplicate (keep latest), log count |
| **Completeness** | All mandatory fields | Required fields non-null | Reject record, partial success for batch |
