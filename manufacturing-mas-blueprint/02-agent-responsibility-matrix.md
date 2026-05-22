# 2. Agent Responsibility Matrix

> Autonomy levels, input/output schemas, escalation paths, fallback behavior, KPI ownership

## 2.1 Agent Overview Table

| # | Agent | Autonomy Level | Primary Function | KPI Owner | Fallback Mode |
|---|-------|---------------|-----------------|-----------|---------------|
| 01 | Procurement | Semi-Autonomous | Raw material sourcing, vendor management, contract negotiation | CPO | Conservative vendor selection, cached price lists |
| 02 | Production & MES | Semi-Autonomous | Machine scheduling, OEE, quality, predictive maintenance | COO | Override to master production schedule (legacy) |
| 03 | Inventory & Warehousing | Full Autonomous | Reorder points, stock rotation, cross-docking | COO/SCM | Safety stock +20% buffer, no dynamic adjustments |
| 04 | Sales & Distribution | Semi-Autonomous | Order routing, fulfillment, logistics, pricing | CSO | Manual order processing via legacy CRM |
| 05 | Market Intelligence | Advisory | Competitive analysis, demand signals, sentiment | CPO/CMO | Last-known-good market snapshot |
| 06 | Predictive Analytics | Advisory | Demand forecasting, scenario simulation | CPO | Ensemble fallback: simple moving average + seasonal decomposition |
| 07 | Financial & Cost Acct | Semi-Autonomous | BOM costing, margin tracking, P&L, cash flow | CFO | Deterministic rule-based engine (always available) |
| 08 | Compliance & Risk | Full Autonomous | Regulatory tracking, risk alerts, audit trails | CRO/CCO | Static rule set, no model-dependent compliance |
| 09 | Orchestrator | Full Autonomous | Governance, arbitration, HITL routing, health monitoring | CIO/CTO | Manual override panel, all agents → Advisory |

## 2.2 Autonomy Level Definitions

| Level | Code | Description | Human Role | Circuit Breaker |
|-------|------|-------------|-----------|-----------------|
| Advisory | L1 | Agent recommends, recommends, human approves/denies | Required for all actions | N/A — human always in loop |
| Semi-Autonomous | L2 | Agent executes within defined bounds; can escalate | Monitor with override capability | Hard thresholds trigger HITL (e.g., price change >5%) |
| Full Autonomous | L3 | Agent executes within bounds; only escalates on errors | Exception-only | Multi-layer: soft threshold (warning) → hard threshold (halt) → circuit breaker (kill switch) |

## 2.3 Detailed Agent Specifications

---

### Agent-01: Procurement Agent

**Autonomy Level**: L2 (Semi-Autonomous)
**KPI Owner**: Chief Procurement Officer (CPO)

**Inputs:**
```json
{
  "erp_po_data": "PostgreSQL/Delta — purchase orders, vendor master",
  "market_prices": "Kafka — raw material spot/futures (LME, Bloomberg)",
  "forecast_demand": "Agent-06 — next 3 months BOM requirements",
  "inventory_levels": "Agent-03 — current raw material stock + safety stock",
  "vendor_esg_scores": "External API — EcoVadis, Sustainalytics",
  "production_schedule": "Agent-02 — upcoming production runs with BOM"
}
```

**Outputs:**
```json
{
  "po_recommendations": "Kafka — optimized order quantities, timing, vendor selection",
  "vendor_scorecards": "Delta — quarterly vendor performance with 15 metrics",
  "price_alerts": "Kafka — >5% price movement with hedging recommendation",
  "contract_terms": "PostgreSQL — negotiated terms, rebates, payment schedules",
  "alt_sourcing_options": "Delta — alternative vendor list with qualification status"
}
```

**Escalation Path:**
1. Price spike >5% → Orchestrator → HITL (CFO/CPO)
2. Vendor quality score <60/100 → Orchestrator → HITL (sourcing team)
3. PO value >$500K → Orchestrator → HITL (procurement director)

**Fallback Behavior:**
- If market feed unavailable: use cached prices (max 24h old) + 3% conservative buffer
- If Agent-06 forecast unavailable: use simple 3-month trailing average
- If Kafka unavailable: queue to local file, replay on reconnect

**Decision Logic:**
```python
def select_vendor(quote_a, quote_b, scores, constraints):
    if score_diff > 0.15:  # 15% quality/ESG score difference
        return higher_score_vendor  # Quality over price
    else:
        return lower_price_vendor   # Price optimized
    # HITL trigger: if PO > $500K or sole-source vendor
```

---

### Agent-02: Production & MES Agent

**Autonomy Level**: L2 (Semi-Autonomous)
**KPI Owner**: Chief Operations Officer (COO)

**Inputs:**
```json
{
  "mes_data": "MES API — machine states, cycle times, OEE, quality data",
  "production_orders": "ERP — planned orders, priorities, due dates",
  "inventory_status": "Agent-03 — material availability for WIP",
  "forecast": "Agent-06 — demand-driven production adjustments",
  "maintenance_schedule": "CMMS — planned maintenance windows",
  "quality_lab_results": "LIMS — in-process and final QC results",
  "shift_calendar": "ERP/HR — planned shifts, downtime schedules, holidays",
  "planned_downtime": "CMMS — scheduled maintenance windows, breaks, changeovers"
}
```

**Outputs:**
```json
{
  "production_schedule": "Kafka — optimized sequence with machine assignments",
  "oee_reports": "Delta — OEE by line, shift, product (availability, performance, quality)",
  "quality_alerts": "Kafka — SPC violations, defect rate > threshold",
  "maintenance_triggers": "Kafka — predictive maintenance alerts with confidence",
  "bottleneck_analysis": "Delta — cycle time analysis, constraint identification",
  "yield_optimization": "Delta — parameter recommendations for yield improvement"
}
```

**Escalation Path:**
1. OEE drops below 70% → Orchestrator → Operations manager alert
2. Quality defect rate >5% → Agent-08 (compliance) + HITL (QA director)
3. Production schedule variance >8 hours → HITL (production manager)

**Fallback Behavior:**
- If MES disconnected: use last-known state with extrapolated cycle times
- If quality data unavailable: assume standard quality, flag for manual inspection
- Schedule optimization unavailable: use FIFO-based legacy schedule

**Predictive Maintenance Model:**
```
Input: vibration, temperature, current draw, run hours, cycle count
Model: XGBoost classifier (binary: failure within N hours)
Confidence threshold: >0.85 → proactive maintenance
                  >0.95 → immediate halt + HITL
```

**Rapid Retraining Trigger:**
```
If OEE drops >10% in 24 hours OR quality defects spike >3σ → 
  trigger unscheduled retraining with expanded window (+6 months historical)
  → HITL if accuracy not restored within 2 retraining cycles
```

---

### Agent-03: Inventory & Warehousing Agent

**Autonomy Level**: L3 (Full Autonomous)
**KPI Owner**: Supply Chain Director

**Inputs:**
```json
{
  "stock_levels": "WMS — real-time inventory by SKU, location, lot",
  "orders": "Agent-04 — sales orders, fulfillment priorities",
  "receipts": "ERP — inbound receipts, expected delivery dates",
  "forecast": "Agent-06 — demand forecast with confidence intervals",
  "production_plan": "Agent-02 — material requirements schedule",
  "supplier_lead_times": "Agent-01 — current supplier performance",
  "expiry_data": "WMS — shelf life / manufactured dates for FEFO"
}
```

**Outputs:**
```json
{
  "reorder_recommendations": "Kafka — dynamic reorder points, EOQ, safety stock",
  "stock_rotation_plan": "Kafka — FIFO/FEFO execution instructions",
  "dead_stock_alerts": "Kafka — inventory with zero movement >90 days",
  "warehouse_optimization": "Delta — slotting optimization, space utilization",
  "cross_dock_instructions": "Kafka — direct ship-from-receiving instructions",
  "inventory_forecast": "Delta — projected stock-out dates at current consumption"
}
```

**Escalation Path:**
1. Stock-out probability >15% within lead time → Orchestrator → CPO alert
2. Dead stock >5% of total inventory value → Orchestrator → finance HITL
3. Space utilization >92% → Orchestrator → warehousing manager

**Fallback Behavior:**
- If WMS unavailable: use cached inventory snapshots from last sync
- If forecast unavailable: reorder point = (max daily usage × max lead time) × 1.5
- Cross-docking disabled: route all receipts to storage first

**Dynamic Safety Stock Formula:**
```
safety_stock = Z × σ_demand × √(avg_lead_time + σ_lead_time) × dynamic_multiplier

Where:
- Z = service level factor (95% = 1.65, 99% = 2.33)
- σ_demand = standard deviation of forecast demand
- dynamic_multiplier = function(forecast_confidence, supplier_reliability)
```

---

### Agent-04: Sales & Distribution Agent

**Autonomy Level**: L2 (Semi-Autonomous)
**KPI Owner**: Chief Sales Officer (CSO)

**Inputs:**
```json
{
  "orders": "CRM + EDI — r
