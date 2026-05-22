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
    consumer_group_id: str = "agent-02-production"
    session_timeout_ms: int = 45000
    heartbeat_interval_ms: int = 3000
    max_poll_interval_ms: int = 300000
    enable_auto_commit: bool = False

    # Topics this agent PRODUCES to
    topic_production_events: str = "events.production"
    topic_dead_letter: str = "events.dead-letter"

    # Topics this agent CONSUMES from
    topic_inventory_events: str = "events.inventory"
    topic_forecast_events: str = "events.forecast"
    topic_orchestrator_events: str = "events.orchestrator"
    topic_market_events: str = "events.market"


class DatabaseSettings(BaseSettings):
    """PostgreSQL and Redis connection settings."""

    model_config = SettingsConfigDict(env_prefix="DB_", env_file=".env")

    postgres_dsn: str = "postgresql+asyncpg://user:pass@localhost:5432/mas_production"
    redis_url: str = "redis://localhost:6379/1"
    pool_min_size: int = 2
    pool_max_size: int = 10


class OEESettings(BaseSettings):
    """OEE calculation weights and thresholds."""

    model_config = SettingsConfigDict(env_prefix="OEE_", env_file=".env")

    # OEE component weights (all must map to 0-100 scale)
    availability_target_pct: float = 90.0
    performance_target_pct: float = 95.0
    quality_target_pct: float = 99.0

    # Thresholds
    oee_critical_threshold_pct: float = 70.0
    quality_defect_critical_pct: float = 5.0
    schedule_variance_hours: float = 8.0

    # Predictive maintenance
    pm_confidence_threshold: float = 0.85
    pm_critical_confidence: float = 0.95

    # Retraining trigger
    retraining_oee_drop_pct: float = 10.0
    retraining_quality_sigma: float = 3.0
    retraining_max_cycles: int = 2

    @field_validator(
        "availability_target_pct",
        "performance_target_pct",
        "quality_target_pct",
    )
    @classmethod
    def check_pct_range(cls, v: float) -> float:
        if not 0.0 <= v <= 100.0:
            raise ValueError(f"Percentage must be between 0.0 and 100.0, got {v}")
        return v


class AgentSettings(BaseSettings):
    """Top-level agent configuration."""

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")

    agent_id: str = "agent-02"
    agent_version: str = "1.0.0"
    log_level: str = "INFO"
    environment: Literal["development", "staging", "production"] = "development"
    config_path: Path = Path("config/agent_config.yaml")

    kafka: KafkaSettings = KafkaSettings()
    database: DatabaseSettings = DatabaseSettings()
    oee: OEESettings = OEESettings()

    # HITL configuration
    hitl_timeout_seconds: int = 3600
    hitl_poll_interval_seconds: int = 10

    # Cache TTLs (seconds)
    cache_ttl_mes_state: int = 300  # 5 minutes
    cache_ttl_production_plan: int = 900  # 15 minutes
    cache_ttl_material_availability: int = 600  # 10 minutes

    # Fallback configuration
    fallback_cycle_time_extrapolation: bool = True

    def load_config_file(self) -> dict:
        """Load additional config from YAML file if it exists."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f) or {}
        return {}


settings = AgentSettings()
