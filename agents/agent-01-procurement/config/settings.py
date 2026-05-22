"""Application configuration via environment variables and YAML overrides."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaSettings(BaseSettings):
    """Kafka connection and topic configuration."""

    model_config = SettingsConfigDict(env_prefix="KAFKA_", env_file=".env")

    bootstrap_servers: str = "localhost:9092"
    consumer_group_id: str = "agent-01-procurement"
    session_timeout_ms: int = 45000
    heartbeat_interval_ms: int = 3000
    max_poll_interval_ms: int = 300000
    enable_auto_commit: bool = False

    # Topics this agent PRODUCES to
    topic_procurement_events: str = "events.procurement"
    topic_dead_letter: str = "events.dead-letter"

    # Topics this agent CONSUMES from
    topic_market_events: str = "events.market"
    topic_forecast_events: str = "events.forecast"
    topic_inventory_events: str = "events.inventory"
    topic_orchestrator_events: str = "events.orchestrator"


class DatabaseSettings(BaseSettings):
    """PostgreSQL and Redis connection settings."""

    model_config = SettingsConfigDict(env_prefix="DB_", env_file=".env")

    postgres_dsn: str = "postgresql+asyncpg://user:pass@localhost:5432/mas_procurement"
    redis_url: str = "redis://localhost:6379/0"
    pool_min_size: int = 2
    pool_max_size: int = 10


class ScoringSettings(BaseSettings):
    """Vendor scoring weights and thresholds."""

    model_config = SettingsConfigDict(env_prefix="SCORING_", env_file=".env")

    # Default weight vector (must sum to 1.0)
    weight_price: float = 0.25
    weight_quality: float = 0.20
    weight_delivery: float = 0.15
    weight_esg: float = 0.10
    weight_financial_health: float = 0.10
    weight_innovation: float = 0.05
    weight_compliance: float = 0.05
    weight_relationship: float = 0.05
    weight_geographic: float = 0.05

    # Thresholds
    min_acceptable_score: float = 60.0
    quality_critical_threshold: float = 70.0  # below this → HITL
    price_spike_warning_pct: float = 5.0
    price_spike_critical_pct: float = 10.0
    po_value_hitl_threshold_usd: float = 500_000.0

    @field_validator("weight_price", "weight_quality", "weight_delivery", "weight_esg",
                     "weight_financial_health", "weight_innovation", "weight_compliance",
                     "weight_relationship", "weight_geographic")
    @classmethod
    def check_weight_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {v}")
        return v


class AgentSettings(BaseSettings):
    """Top-level agent configuration."""

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")

    agent_id: str = "agent-01"
    agent_version: str = "1.0.0"
    log_level: str = "INFO"
    environment: Literal["development", "staging", "production"] = "development"
    config_path: Path = Path("config/agent_config.yaml")

    kafka: KafkaSettings = KafkaSettings()
    database: DatabaseSettings = DatabaseSettings()
    scoring: ScoringSettings = ScoringSettings()

    # HITL configuration
    hitl_timeout_seconds: int = 3600  # default SLA for HITL response
    hitl_poll_interval_seconds: int = 10

    # Cache TTLs (seconds)
    cache_ttl_market_prices: int = 14400  # 4 hours
    cache_ttl_vendor_master: int = 86400  # 24 hours
    cache_ttl_forecast: int = 3600  # 1 hour

    # Fallback configuration
    fallback_price_buffer_pct: float = 3.0
    fallback_forecast_months: int = 3

    def load_config_file(self) -> dict:
        """Load additional config from YAML file if it exists."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f) or {}
        return {}


settings = AgentSettings()
