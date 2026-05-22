# 3. Recommended Tech Stack

> Production-grade, vendor-agnostic, open-standards-based technology architecture

## 3.1 Stack Overview

| Layer | Technology | Version | Justification | Alternatives Considered |
|-------|-----------|---------|--------------|------------------------|
| **Agent Orchestration** | LangGraph + CrewAI | LangGraph ≥0.2, CrewAI ≥0.30 | State-graph architecture with checkpointing; CrewAI for task delegation patterns | AutoGen (too Microsoft-centric), Semantic Kernel (less mature) |
| **LLM Gateway** | LiteLLM | ≥1.40 | Model-agnostic routing (cost/latency/accuracy); supports 100+ providers | LangChain (vendor lock-in), Portkey (less transparent) |
| **Message Bus** | Apache Kafka | ≥3.6 | Industry standard for event streaming; exactly-once semantics, schema registry | Pulsar (less ecosystem), RabbitMQ (no log compaction) |

**Kafka Alternative Strategy**: All messaging abstracted behind CloudEvents interface. Migration path to Apache Pulsar documented (same pub/sub model, compatible topic structure). NATS considered for edge/low-connectivity deployments.
| **Data Lakehouse** | Delta Lake + Apache Iceberg | Delta 3.1, Iceberg 1.5 | ACID transactions on data lake; time travel, schema evolution | Hudi (less adoption), Snowflake (vendor lock-in) |
| **Time-Series DB** | InfluxDB | ≥3.0 | Purpose-built for IoT/sensor/machine data; Flux query language | TimescaleDB (PostgreSQL extension), Prometheus (limited retention) |
| **Relational DB** | PostgreSQL | ≥16 | Enterprise-grade ACID, JSONB support, pg_partman for partitioning | CockroachDB (distributed but complex), MySQL (less advanced SQL) |
| **Document Store** | MongoDB | ≥7.0 | Flexible schema for market intelligence, unstructured data | Couchbase (less adoption), DynamoDB (AWS lock-in) |
| **Cache** | Redis | ≥7.2 | Sub-millisecond latency for feature store, session state, rate limiting | Memcached (no persistence), Hazelcast (heavyweight) |
| **Object Store** | MinIO | ≥2024 | S3-compatible, self-hosted, immutable bucket support for audit logs | AWS S3 (cloud lock-in), Ceph (too complex for this use case) |
| **Stream Processing** | Apache Flink / ksqlDB | Flink 1.18 | Real-time aggregations, pattern matching, CEP | Spark Streaming (micro-batch, not true streaming) |
| **Batch ETL** | Apache Airflow + dbt | Airflow 2.8, dbt 1.7 | Orchestration + data transformation; dbt for analytics engineering | Prefect (less community), Dagster (newer, less mature) |
| **Data Quality** | Great Expectations + Deequ | GX ≥0.18, Deequ 2.0 | Automated data quality gates, profiling, documentation | Soda (less adoption), dbt-expectations (too light) |
| **Data Lineage** | OpenLineage + Marquez | OpenLineage 1.12 | End-to-end lineage tracking, impact analysis | Atlan (SaaS lock-in), Collibra (expensive) |
| **Model Registry** | MLflow | ≥2.10 | Model versioning, deployment, drift monitoring | Weights & Biases (cloud lock-in), Kubeflow (heavyweight) |
| **Model Monitoring** | Evidently AI | ≥0.4 | Drift detection, model performance, data quality | WhyLabs (cloud lock-in), NannyML (less features) |
| **Feature Store** | Redis + Feast | Feast ≥0.35 | Online (Redis) + offline (Delta) feature serving | Tecton (cloud lock-in), SageMaker Feature Store (AWS lock-in) |
| **Monitoring** | Prometheus + Grafana | Prom 2.50, Grafana 10 | Industry standard metrics, alerting, dashboards | Datadog (expensive), New Relic (expensive) |
| **Tracing** | OpenTelemetry | ≥1.25 | Distributed tracing across agents, standardized instrumentation | Jaeger (standalone, less integration) |
| **Security** | OPA/Gatekeeper + HashiCorp Vault + Sigstore | OPA 0.60, Vault 1.16 | Policy-as-code, secrets management, artifact signing | Kyverno (K8s-only), CyberArk (expensive) |
| **API Gateway** | Kong / APISIX | Kong 3.6 | Rate limiting, auth, routing, observability | NGINX (no native API management), Envoy (too low-level) |
| **Container Runtime** | Kubernetes + Helm | K8s 1.29 | Container orchestration, auto-scaling, self-healing | Docker Swarm (limited), Nomad (less ecosystem) |
| **CI/CD** | GitLab CI / GitHub Actions | — | Pipeline automation, model deployment, infra-as-code | Jenkins (legacy), ArgoCD (CD only) |
| **Secrets Management** | HashiCorp Vault | ≥1.16 | Dynamic secrets, encryption-as-a-service, audit logging | AWS Secrets Manager (lock-in), Azure Key Vault (lock-in) |

## 3.2 LLM Routing Strategy (LiteLLM)

```
User Query / Agent Task
        │
        ▼
┌─────────────────────────────────┐
│        LiteLLM Router            │
│  ┌─────────────────────────────┐ │
│  │  Routing Rules:              │ │
│  │  • Forecasting → GPT-4o     │ │
│  │  • Optimization → Claude 3  │ │
│  │  • Classification → GPT-4o- │ │
│  │    mini / Llama 3           │ │
│  │  • Summarization → Claude   │ │
│  │    Haiku / Gemini Flash     │ │
│  │  • Code generation → Claude │ │
│  │  • Structured extraction →  │ │
│  │    GPT-4o-mini              │ │
│  └─────────────────────────────┘ │
│  Cost/Latency/Accuracy trade-offs│
│  Fallback chain: Primary → Alt → │
│  Local (quantized)              │
└─────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────┐
│    Fallback: Local Models        │
│  • Quantized Llama 3.1 8B       │
│  • Mistral 7B (low latency)     │
│  • Phi-3-mini (edge devices)    │
└─────────────────────────────────┘
```

**Cost Control Rules:**
- Forecasting tasks: use GPT-4o (high accuracy needed) — budget 40% of AI compute
- Classification/Extraction: use GPT-4o-mini — budget 25%
- Summarization: use Claude Haiku — budget 15%
- Fallback to local quantized models when API costs exceed 0.5% of marginal profit gain
- Weekly cost review against margin improvement; auto-downgrade expensive models if threshold breached

## 3.3 Data Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                    DATA LAKEHOUSE (Delta Lake + Iceberg)            │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Bronze Layer (Raw Ingestion)                                │  │
│  │  • Raw Kafka topics as Delta tables                          │  │
│  │  • Immutable, append-only                                    │  │
│  │  • Full data quality pass-through (flagged, not filtered)    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Silver Layer (Cleaned & Enriched)                           │  │
│  │  • Data quality passed, deduplicated                         │  │
│  │  • Joins, aggregations, feature engineering                  │  │
│  │  • dbt transformations with documentation                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Gold Layer (Business-Ready)                                 │  │
│  │  • Aggregated fact tables                                    │  │
│  │  • Materialized views for dashboards                         │  │
│  │  • Agent-consumable feature tables                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  Storage: MinIO (S3-compatible, self-hosted, WORM for audit)       │
│  Catalog: Apache Hive Metastore / Unity Catalog                    │
│  Lineage: OpenLineage → Marquez Dashboard                          │
│  Versioning: DVC for model data, Delta time travel for tables      │
└────────────────────────────────────────────────────────────────────┘
```

## 3.4 Deployment Architecture

```
                         ┌──────────────────────┐
                         │  Load Balancer (HA)   │
                         └──────┬─────────────┬──┘
                                │             │
                   ┌────────────▼──┐   ┌──────▼────────────┐
                   │  API Gateway  │   │  Web Dashboard    │
                   │   (Kong)      │   │  (Grafana/React)  │
                   └────────────┬──┘   └───────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
    ┌─────▼─────┐        ┌─────▼─────┐        ┌─────▼─────┐
    │ Agent Pod │        │ Agent Pod │        │ Agent Pod │
    │ (K8s)     │  ...   │ (K8s)     │  ...   │ (K8s)     │
    │ 1-10 reps │        │ 1-10 reps │        │ 1-10 reps │
    └─────┬─────┘        └─────┬─────┘        └─────┬─────┘
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Service Mesh (Istio) │
                    │  mTLS, traffic mgmt   │
                    └───────────────────────┘

    ┌────────────────────────────────────────────────────────────────┐
    │                      Data Tier                                 │
    │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌─────────────┐ │
    │  │ Kafka  │ │ Delta  │ │Postgres│ │ Redis  │ │   MinIO     │ │
    │  │ Cluster│ │ Lake   │ │Primary │ │Cluster │ │(Object Str) │ │
    │  └────────┘ └────────┘ └────────┘ └────────┘ └─────────────┘ │
    └────────────────────────────────────────────────────────────────┘
```

## 3.5 Open Standards & Interoperability

| Standard | Usage | Compliance Required |
|----------|-------|-------------------|
| **CloudEvents 1.0** | All agent-to-agent messaging | Yes — non-negotiable |
| **OpenAPI 3.1** | All REST API definitions | Yes — non-negotiable |
| **AsyncAPI 2.6** | Event/channel documentation | Yes — non-negotiable |
| **MLflow Model Registry** | Model packaging, versioning, deployment | Yes — non-negotiable |
| **OpenLineage** | Data lineage throughout pipeline | Yes — non-negotiable |
| **OpenTelemetry** | Distributed tracing, metrics | Yes — non-negotiable |
| **JSON-LD 1.1** | Semantic message payloads with @context | Yes — non-negotiable |
| **Prometheus Exposition** | Metrics format | Yes — non-negotiable |
| **OPA Rego** | Policy-as-code rules | Yes — non-negotiable |
| **SCIM 2.0** | User/role provisioning | Recommended |
| **SAML 2.0 / OIDC** | SSO authentication | Yes — non-negotiable |

## 3.6 Cost Estimation (Monthly Run Rate)

| Component | Estimated Monthly Cost | Notes |
|-----------|----------------------|-------|
| Kubernetes cluster (3 nodes × 8 vCPU, 32GB) | $1,200 – $2,400 | On-prem or cloud (AWS EKS / GKE) |
| Kafka cluster (3 brokers) | $600 – $1,200 | Confluent Cloud or self-managed |
| Delta Lake storage (10 TB) | $200 – $500 | MinIO self-hosted storage |
| PostgreSQL (HA, 500GB) | $300 – $600 | Self-managed or RDS equivalent |
| InfluxDB (time-series, 1TB) | $200 – $400 | Self-hosted |
| Redis cluster (HA, 16GB) | $150 – $300 | Self-hosted or ElastiCache |
| LLM API costs | $2,000 – $8,000 | Depends on volume; target <0.5% of margin gain |
| Monitoring (Prometheus + Grafana) | $100 – $200 | Self-hosted |
| CI/CD infrastructure | $200 – $500 | Self-hosted runners |
| **Total estimated monthly** | **$4,950 – $14,100** | Scales with transaction volume |

**Cost control mechanisms:**
- LLM inference costs capped at 0.5% of marginal profit improvement
- Auto-scaling agents based on queue depth (idle agents → zero replicas)
- Local quantized models for non-critical tasks (save ~60% LLM costs)
- Data lifecycle policies: bronze (7d), silver (90d), gold (365d), archive (7yr WORM)

---

*See also: [Integration: Data Lakehouse](../integration/data-lakehouse-architecture.md) | [Security: Zero Trust](../security/zero-trust-architecture.md)*
