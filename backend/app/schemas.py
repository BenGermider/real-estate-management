from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserInfo(BaseModel):
    user_id: str
    email: EmailStr
    roles: List[str]


class DatasetItem(BaseModel):
    id: str
    source: str
    title: str
    description: Optional[str]
    last_updated: Optional[str]


class DatasetDetail(BaseModel):
    id: str
    source: str
    title: str
    description: Optional[str]
    schema: dict | None
    last_updated: Optional[str]
    sample: dict | None


class DatasetListResponse(BaseModel):
    items: List[DatasetItem]
    total: int


class IngestRequestACS(BaseModel):
    year: int
    state_fips: Optional[str] = None
    county_fips: Optional[str] = None
    force: Optional[bool] = False


class IngestRequestHUD(BaseModel):
    year: int
    force: Optional[bool] = False


class IngestJobResponse(BaseModel):
    job_id: str
    status: str
    type: Optional[str] = None
    submitted_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    message: Optional[str] = None
    output_uri: Optional[str] = None


class RegionItem(BaseModel):
    region_id: str
    name: str
    type: str
    state_fips: str
    county_fips: Optional[str] = None


class RegionListResponse(BaseModel):
    items: List[RegionItem]
    total: int


class RegionMetrics(BaseModel):
    region_id: str
    year: int
    median_household_income: float
    median_gross_rent: float
    rent_to_income_ratio: float
    vacancy_rate: float | None = None
    hud_fmr_2br: float | None = None
    population: int | None = None
    sources: List[str]


class RegionTimeseriesItem(BaseModel):
    year: int
    median_household_income: float | None = None
    median_gross_rent: float | None = None
    hud_fmr_2br: float | None = None
    rent_to_income_ratio: float | None = None


class RegionTimeseriesResponse(BaseModel):
    region_id: str
    series: List[RegionTimeseriesItem]


class InsightCallout(BaseModel):
    metric: str
    delta: float
    direction: str


class RegionInsight(BaseModel):
    region_id: str
    year: int
    affordability_quartile: str
    trend: str
    callouts: List[InsightCallout]
    narrative: str


class CompareRegionItem(BaseModel):
    region_id: str
    name: str
    year: int
    median_household_income: float | None = None
    median_gross_rent: float | None = None
    hud_fmr_2br: float | None = None
    rent_to_income_ratio: float | None = None


class CompareRegionsResponse(BaseModel):
    regions: List[CompareRegionItem]


class HealthResponse(BaseModel):
    status: str
    version: str

