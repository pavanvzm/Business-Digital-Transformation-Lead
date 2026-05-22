"""Application configuration for Agent-03 (Inventory & Warehousing)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KAFKA_", env_file=".env")
    bootstrap_servers: str = "localhost:9092"
    consumer_group_id: str = "agent-03-inventory"
    session_timeout_ms: int = 45000
    heartbeat_interval_ms: int = 3000
    max_poll_interval_ms: int = 300000
    enable_auto_commit: bool = False
    topic_inventory_events: str = "events.inventory"
    topic_dead_letter: str = "events.dead-letter"
    topic_orchestrator_events: str = "events.orchestrator"
    topic_production_events: str = "events.production"
    topic_forecast_events: str = "events.forecast"
    topic_procurement_events: str = "events.procurement"
    topic_sales_events: str = "events.sales"


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_", env_file=".env")
    postgres_dsn: str = "postgresql+asyncpg://user:pass@localhost:5432/mas_inventory"
    redis_url: str = "redis://localhost:6379/2"
    pool_min_size: int = 2
    pool_max_size: int = 10


class InventorySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INV_", env_file=".env")

    # Service level factor (Z-score)
    service_level_pct: float = 95.0  # Z=1.65 default
    safety_stock_buffer_pct: float = 20.0  # Fallback buffer
    dead_stock_days: int = 90
    space_utilization_warning_pct: float = 85.0
    space_utilization_critical_pct: float = 92.0
    stock_out_probability_hitl: float = 0.15
    dead_stock_value_hitl_pct: float = 5.0
    reorder_point_dynamic: bool = True
    eoq_model_enabled: bool = True
    cross_docking_enabled: bool = True


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")
    agent_id: str = "agent-03"
    agent_version: str = "1.0.0"
    log_level: str = "INFO"
    environment: Literal["development", "staging", "production"] = "development"
    config_path: Path = Path("config/agent_config.yaml")
    kafka: KafkaSettings = KafkaSettings()
    database: DatabaseSettings = DatabaseSettings()
    inventory: InventorySettings = InventorySettings()
    hitl_timeout_seconds: int = 3600
    hitl_poll_interval_seconds: int = 10

    def load_config_file(self) -> dict:
        if self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f) or {}
        return {}


settings = AgentSettings()
