from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError

from ..config import Settings
from ..logger import get_logger

settings = Settings()
logger = get_logger(__name__)


class BigQueryClient:
    def __init__(self) -> None:
        self.dataset = settings.bigquery_dataset
        self.project = settings.bigquery_project
        try:
            self.client = bigquery.Client(project=self.project)
        except Exception as exc:  # pragma: no cover - offline fallback
            logger.warning("BigQuery client init failed; running without BigQuery", error=str(exc))
            self.client = None

    async def fetch_latest_metrics(self, region_id: str):
        if not self.client:
            return None
        query = f"""
        SELECT *
        FROM `{self.project}.{self.dataset}.region_metrics_latest`
        WHERE region_id = @region_id
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("region_id", "STRING", region_id)]
        )
        try:
            result = self.client.query(query, job_config=job_config).result()
            for row in result:
                return dict(row)
            return None
        except GoogleAPIError as exc:
            logger.error("BigQuery metrics query failed", error=str(exc))
            return None

    async def fetch_timeseries(self, region_id: str, start_year: int | None, end_year: int | None):
        if not self.client:
            return []
        filters = ["region_id = @region_id"]
        params = [bigquery.ScalarQueryParameter("region_id", "STRING", region_id)]
        if start_year:
            filters.append("year >= @start_year")
            params.append(bigquery.ScalarQueryParameter("start_year", "INT64", start_year))
        if end_year:
            filters.append("year <= @end_year")
            params.append(bigquery.ScalarQueryParameter("end_year", "INT64", end_year))
        where_clause = " AND ".join(filters)
        query = f"""
        SELECT year, median_household_income, median_gross_rent, hud_fmr_2br, rent_to_income_ratio
        FROM `{self.project}.{self.dataset}.region_metrics_timeseries`
        WHERE {where_clause}
        ORDER BY year
        """
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        try:
            result = self.client.query(query, job_config=job_config).result()
            return [dict(row) for row in result]
        except GoogleAPIError as exc:
            logger.error("BigQuery timeseries query failed", error=str(exc))
            return []

