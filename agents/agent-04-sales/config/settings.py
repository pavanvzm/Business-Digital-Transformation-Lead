"""Application configuration for Agent-04 (Sales & Distribution)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KAFKA_", env_file=".env")
    bootstrap_servers: str = "localhost:9092"
    consumer_group_id: str = "agent-04-sales"
    session_timeout_ms: int = 45000
    heartbeat_interval_ms: int = 3000
    max_poll_interval_ms: int = 300000
    enable_auto_commit: bool = False
    topic_sales_events: str = "events.sales"
    topic_dead_letter: str = "events.dead-letter"
    topic_orchestrator_events: str = "events.orchestrator"
    topic_inventory_events: str = "events.inventory"
    topic_market_events: str = "events.market"
    topic_production_events: str = "events.production"


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_", env_file=".env")
    postgres_dsn: str = "postgresql+asyncpg://user:pass@localhost:5432/mas_sales"
    redis_url: str = "redis://localhost:6379/3"
    pool_min_size: int = 2
    pool_max_size: int = 10


class SalesSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SALES_", env_file=".env")
    pricing_change_hitl_pct: float = 5.0
    bulk_order_minimum_usd: float = 100_000.0
    fulfillment_priority_method: str = "edf"  # Earliest Due First
    allocation_hitl_threshold_pct: float = 10.0
    customer_tier_premium_threshold: int = 1
    logistics_optimization_enabled: bool = True


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")
    agent_id: str = "agent-04"
    agent_version: str = "1.0.0"
    log_level: str = "INFO"
    environment: Literal["development", "staging", "production"] = "development"
    config_path: Path = Path("config/agent_config.yaml")
    kafka: KafkaSettings = KafkaSettings()
    database: DatabaseSettings = DatabaseSettings()
    sales: SalesSettings = SalesSettings()
    hitl_timeout_seconds: int = 3600
    hitl_poll_interval_seconds: int = 10

    def load_config_file(self) -> dict:
        if self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f) or {}
        return {}


settings = AgentSettings()
