import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Enum, JSON, String, Text, Float, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    roles = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(64), primary_key=True)
    source = Column(Enum("acs", "hud", name="dataset_source"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    schema = Column(JSON, nullable=True)
    sample = Column(JSON, nullable=True)
    last_updated = Column(DateTime, nullable=True)


class IngestJob(Base):
    __tablename__ = "ingest_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum("acs", "hud", name="ingest_type"), nullable=False)
    status = Column(Enum("queued", "running", "succeeded", "failed", name="ingest_status"), nullable=False, default="queued")
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    message = Column(Text, nullable=True)
    output_uri = Column(Text, nullable=True)
    params = Column(JSON, nullable=True)


class Region(Base):
    __tablename__ = "regions"

    region_id = Column(String(32), primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(Enum("county", "state", "msa", name="region_type"), nullable=False)
    state_fips = Column(String(2), nullable=False)
    county_fips = Column(String(3), nullable=True)

    __table_args__ = (
        UniqueConstraint("state_fips", "county_fips", name="uix_state_county"),
    )


class MetricsCache(Base):
    __tablename__ = "metrics_cache"
    __table_args__ = (UniqueConstraint("region_id", "year", name="uix_region_year"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_id = Column(String(32), nullable=False)
    year = Column(Integer, nullable=False)
    median_household_income = Column(Float, nullable=True)
    median_gross_rent = Column(Float, nullable=True)
    rent_to_income_ratio = Column(Float, nullable=True)
    vacancy_rate = Column(Float, nullable=True)
    hud_fmr_2br = Column(Float, nullable=True)
    population = Column(Integer, nullable=True)
    sources = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

