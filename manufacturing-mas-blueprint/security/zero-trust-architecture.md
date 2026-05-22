# Security: Zero-Trust Architecture

> Defense-in-depth security framework for manufacturing multi-agent system

## Zero-Trust Principles

```
┌────────────────────────────────────────────────────────────────────┐
│                    ZERO-TRUST ARCHITECTURE                          │
│                                                                      │
│  Principle 1: Verify Explicitly                                     │
│  • Every request authenticated and authorized                       │
│  • mTLS between all services                                        │
│  • JWT with audience/scope validation                               │
│  • No implicit trust based on network location                      │
│                                                                      │
│  Principle 2: Least Privilege Access                                │
│  • RBAC: Role-based access for humans                               │
│  • ABAC: Attribute-based access for agents                          │
│  • Just-in-time (JIT) privilege elevation                           │
│  • Automatic credential rotation (Vault)                            │
│                                                                      │
│  Principle 3: Assume Breach                                         │
│  • End-to-end encryption (AES-256 at rest, TLS 1.3 in transit)      │
│  • Continuous validation, not just at perimeter                     │
│  • Audit logging for every access                                   │
│  • Anomaly detection on access patterns                             │
│  • WORM storage for immutable audit trails                          │
└────────────────────────────────────────────────────────────────────┘
```

## Security Architecture Layers

| Layer | Controls | Technologies |
|-------|----------|-------------|
| **Network** | Network segmentation, micro-segmentation, egress filtering | Istio service mesh, Calico network policies |
| **API Gateway** | Rate limiting, authentication, IP allowlisting | Kong / APISIX |
| **Service Mesh** | mTLS, traffic encryption, circuit breaking | Istio with mTLS |
| **Authentication** | OIDC, SSO, MFA for humans; Service accounts + mTLS for agents | Keycloak / Dex, Vault |
| **Authorization** | RBAC (humans) + ABAC (agents), policy-as-code | OPA / Gatekeeper |
| **Secrets** | Dynamic secrets, rotation, encryption | HashiCorp Vault |
| **Data at Rest** | AES-256 encryption, key rotation | MinIO SSE-S3, Delta Lake encryption |
| **Data in Transit** | TLS 1.3, mTLS, Kafka SSL | Istio, Kafka SSL |
| **Audit** | Immutable logs, chain-of-custody, tamper-evident | WORM storage (MinIO object lock) |
| **Monitoring** | SIEM, threat detection, anomaly detection | ELK / Splunk, Falco |

## RBAC Matrix (Human Users)

| Role | Dashboards | HITL Approvals | Agent Config | Audit Logs | System Admin |
|------|-----------|---------------|-------------|-----------|-------------|
| **Viewer** (Read-only) | View | None | None | None | None |
| **Analyst** | View + Export | None | None | View | None |
| **Operations Manager** | View + Export | Production, Inventory | Production parameters | View | None |
| **Supply Chain Manager** | View + Export | Procurement, Inventory | Procurement, Inventory | View | None |
| **Sales Director** | View + Export | Pricing (<5%) | Pricing rules | View | None |
| **CFO** | All + Export | Financial close, Budget >5% | Financial parameters | View + Export | None |
| **CPO** | All + Export | Supplier onboarding, Forecast | All planning | View + Export | None |
| **COO** | All + Export | Production override | All production | View + Export | None |
| **CRO/CCO** | All + Export | Compliance decisions | Compliance rules | Full access | None |
| **System Administrator** | All | Kill switch | All | Full access | Full |
| **Auditor** | View only | None | None | Full read-only | None |

## Secrets Management (HashiCorp Vault)

```
┌────────────────────────────────────────────────────────────────────┐
│                   VAULT SECRETS ARCHITECTURE                        │
│                                                                      │
│  Dynamic Secrets:                                                    │
│  • PostgreSQL: 24h lease, auto-rotated                              │
│  • Kafka: 12h lease, auto-rotated (SASL/SCRAM)                     │
│  • API Keys: 7d rotation, manual approval for change                │
│                                                                      │
│  Static Secrets:                                                     │
│  • ERP passwords: quarterly rotation, human approval                │
│  • Banking API keys: monthly rotation, CFO approval                 │
│  • LLM API keys: 90d rotation, auto-rotated                         │
│                                                                      │
│  Encryption Keys:                                                    │
│  • Data encryption keys (DEK): auto-rotated monthly                 │
│  • Key encryption keys (KEK): manual rotation, annual               │
│  • Master key: HSM-backed, offline storage                          │
│                                                                      │
│  Policies:                                                           │
│  • Agent-01 → read: erp/*, market/prices; write: procurement/*     │
│  • Agent-02 → read: mes/*, erp/production; write: production/*     │
│  • Agent-07 → read: erp/finance, banking/*; write: finance/*       │
│  • Agent-09 → read: all; write: governance/*                       │
└────────────────────────────────────────────────────────────────────┘
```

## Encryption Standards

| Data State | Standard | Key Management | Notes |
|-----------|----------|---------------|-------|
| **At Rest — Data Lake** | AES-256 (SSE-S3) | Vault + MinIO KMS | Per-bucket keys |
| **At Rest — PostgreSQL** | TDE (AES-256) | Vault + pg_tde | Column-level encryption for PII |
| **At Rest — Kafka Logs** | TLS encryption + at-rest encryption | Vault + Kafka | Per-topic keys |
| **At Rest — WORM Audit** | AES-256 + object lock | Vault + MinIO | Immutable, 7-year retention |
| **In Transit — Internal** | TLS 1.3 | Istio mTLS certs | Auto-rotated (90d) |
| **In Transit — External** | TLS 1.3 | Public CA certs | Mutual auth for B2B APIs |
| **Backup** | AES-256 | Separate backup key | Offline storage |
