from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List


class Settings(BaseSettings):
    database_url: str = Field(..., alias="DATABASE_URL")
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_expires_seconds: int = Field(3600, alias="JWT_EXPIRES_SECONDS")
    admin_email: str = Field(..., alias="ADMIN_EMAIL")
    admin_password: str = Field(..., alias="ADMIN_PASSWORD")

    backend_port: int = Field(8000, alias="BACKEND_PORT")


    postgres_db: str = Field(..., alias="POSTGRES_DB")
    postgres_host: str = Field(..., alias="POSTGRES_HOST")
    postgres_port: int = Field(..., alias="POSTGRES_PORT")

    gcp_project: str = Field("local-project", alias="GCP_PROJECT")
    pubsub_emulator_host: str | None = Field(None, alias="PUBSUB_EMULATOR_HOST")
    pubsub_topic_ingestion: str = Field("ingestion-jobs", alias="PUBSUB_TOPIC_INGESTION")
    pubsub_topic_status: str = Field("ingestion-status", alias="PUBSUB_TOPIC_STATUS")

    bigquery_dataset: str = Field("rem_analytics", alias="BIGQUERY_DATASET")
    bigquery_project: str = Field("local-project", alias="BIGQUERY_PROJECT")

    acs_latest_year: int = Field(2022, alias="ACS_LATEST_YEAR")
    hud_latest_year: int = Field(2024, alias="HUD_LATEST_YEAR")
    bootstrap_states: List[str] = Field(default_factory=list, alias="BOOTSTRAP_STATES")
    bootstrap_enabled: bool = Field(True, alias="BOOTSTRAP_ENABLED")

    @field_validator("bootstrap_states", mode="before")
    @classmethod
    def split_states(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v or []

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

