# Integration: ERP & System Connectors

> Enterprise system integration patterns, dual-write strategy, and connector specifications

## Connector Matrix

| System | Protocol | Data Direction | Sync Frequency | Volume | Criticality |
|--------|----------|---------------|----------------|--------|-------------|
| **SAP S/4HANA** | RFC / OData / Kafka | Bidirectional | Real-time (events) + Batch (daily) | 50K msg/day | Critical |
| **Oracle EBS** | REST / SOAP / Kafka | Bidirectional | Real-time + Batch | 40K msg/day | Critical |
| **MES (Siemens OpCenter)** | MQTT / OPC-UA | Read (primary) + Write (schedule) | Real-time (10Hz telemetry) | 1M msg/day | Critical |
| **WMS (Manhattan)** | REST API | Read (inventory) + Write (orders) | 5-min polling + events | 20K msg/day | High |
| **CRM (Salesforce)** | REST / Streaming API | Read (orders, customers) + Write (pricing) | 15-min polling + events | 15K msg/day | High |
| **TMS (Oracle TMS)** | REST API | Read (rates, status) | Hourly | 5K msg/day | Medium |
| **CMMS (Maximo)** | REST API | Read (maintenance schedule) | Hourly | 2K msg/day | Medium |
| **LIMS (LabVantage)** | REST API | Read (QC results) | 30-min polling | 1K msg/day | High |
| **Banking APIs** | REST (SFTP for statements) | Read-only | Daily (statements) + Real-time (payments) | 500 msg/day | Critical |
| **Market Data Feeds** | WebSocket / REST | Read-only | Real-time (prices) + Daily (reports) | 100K msg/day | Medium |
| **POS / Retailer EDI** | EDI 850/856/810 / REST | Read (orders) + Write (invoices) | Real-time (EDI) + Hourly (API) | 10K msg/day | High |

## Dual-Write Strategy

```
┌────────────────────────────────────────────────────────────────────┐
│                       DUAL-WITE PATTERN                             │
│                                                                      │
│  MAS Decision                                                       │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    WRITE MANAGER                              │   │
│  │  ┌─────────────────────────────────────────────────────────┐ │   │
│  │  │  1. Write to MAS Delta Lake (primary)                   │ │   │
│  │  │     • Transaction ID: TXN-XXXX                          │ │   │
│  │  │     • Agent: Agent-XX                                    │ │   │
│  │  │     • Decision: full payload with provenance             │ │   │
│  │  └─────────────────────────────────────────────────────────┘ │   │
│  │                              │                                 │   │
│  │  ┌─────────────────────────────────────────────────────────┐ │   │
│  │  │  2. Write to Legacy ERP/MES (shadow)                   │ │   │
│  │  │     • Map to legacy schema                              │ │   │
│  │  │     • Use legacy API with retry                         │ │   │
│  │  │     • If legacy unavailable → queue for retry           │ │   │
│  │  │     • Max 3 retries → dead-letter → HITL               │ │   │
│  │  └─────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  RECONCILIATION JOB (Daily at 02:00)                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  SELECT                                                      │   │
│  │    source_system, record_type, COUNT(*) as total,            │   │
│  │    SUM(CASE WHEN mas_val = legacy_val THEN 1 ELSE 0 END)     │   │
│  │      as matched,                                             │   │
│  │    SUM(CASE WHEN mas_val != legacy_val THEN 1 ELSE 0 END)    │   │
│  │      as mismatched                                           │   │
│  │  FROM reconciliation_daily                                   │   │
│  │  WHERE date = CURRENT_DATE                                   │   │
│  │  GROUP BY source_system, record_type                          │   │
│  │  HAVING match_rate < 0.99                                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

## SAP Connector Specification

```
Connector: sap-kafka-connect
Protocol: SAP OData (for CRUD) + RFC (for BAPI calls)
Authentication: SAP Service User with limited role
Topics:
  ──> erp.sap.purchase_orders      (Source: SAP → Kafka)
  ──> erp.sap.production_orders    (Source: SAP → Kafka)
  ──> erp.sap.financial_postings   (Source: SAP → Kafka)
  ──> erp.sap.material_master      (Source: SAP → Kafka)
  <── erp.sap.po_updates           (Sink: Kafka → SAP BAPI)
  <── erp.sap.schedule_updates     (Sink: Kafka → SAP PP)

Error Handling:
  - Retry: 3 attempts (exponential backoff: 5s, 30s, 5min)
  - Dead-letter topic: erp.sap.dlq
  - Alert: if >10 errors in 1 hour → Orchestrator alert

Schema:
  - Avro schema with Confluent Schema Registry
  - Backward-compatible evolution
  - Each message includes: source_timestamp, source_user, change_indicator
```

## Low-Connectivity Fallback Mode

```
TRIGGER: Network connectivity loss >30s OR ERP/MES API unavailable

FALLBACK PROTOCOL:
1. All agents immediately drop to L0 (manual) or L1 (advisory with cached data)
2. Source: last-known-good cached data (max 24h old)
3. Predictions: use locally cached quantized models (see tech-stack)
4. Inventory: use conservative safety stock rules (multiply by 1.2)
5. Production: revert to master production schedule (last synchronized)
6. Orders: queue outgoing messages locally with timestamps
7. Reconnect: replay queued messages in order using Kafka idempotent producer

CACHE FRESHNESS:
  - Market prices: 4 hours (stale → use +5% buffer)
  - Inventory levels: 1 hour
  - Customer data: 24 hours
  - Machine states: 5 minutes
  - Forecasts: 24 hours (use with confidence penalty)
```
