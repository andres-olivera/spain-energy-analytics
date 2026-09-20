"""HTTP client and date-window helpers for Red Eléctrica's REData API."""

from __future__ import annotations

import calendar
from collections.abc import Iterator
from datetime import date, datetime, time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import (
    BASE_URL,
    DATASETS,
    DEFAULT_LANGUAGE,
    DEFAULT_TIMEOUT_SECONDS,
    PENINSULAR_GEO_PARAMS,
)


class REDataAPIError(RuntimeError):
    """Raised when REData returns an invalid or unsuccessful response."""


def month_windows(start: date, end: date) -> Iterator[tuple[datetime, datetime]]:
    """Yield inclusive calendar-month windows between two dates.

    Chunking API requests keeps downloads predictable and avoids relying on large
    date ranges that some REData widgets handle inconsistently.
    """

    if start > end:
        raise ValueError("start must be on or before end")

    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        month_start = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        month_end = date(year, month, last_day)

        chunk_start = max(start, month_start)
        chunk_end = min(end, month_end)
        yield (
            datetime.combine(chunk_start, time.min),
            datetime.combine(chunk_end, time(23, 59)),
        )

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1


class REDataClient:
    """Small, retry-aware client for the public REData REST API."""

    def __init__(
        self,
        base_url: str = BASE_URL,
        language: str = DEFAULT_LANGUAGE,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.language = language
        self.timeout = timeout
        self.session = session or self._build_session()

    @staticmethod
    def _build_session() -> requests.Session:
        retry = Retry(
            total=4,
            connect=4,
            read=4,
            status=4,
            backoff_factor=0.8,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            respect_retry_after_header=True,
        )
        session = requests.Session()
        session.mount("https://", HTTPAdapter(max_retries=retry))
        session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "spain-energy-analytics/0.1",
            }
        )
        return session

    def fetch(
        self,
        dataset: str,
        start: datetime,
        end: datetime,
        time_trunc: str | None = None,
    ) -> dict:
        """Fetch one date chunk for a configured dataset."""

        if dataset not in DATASETS:
            allowed = ", ".join(sorted(DATASETS))
            raise ValueError(f"Unknown dataset '{dataset}'. Choose one of: {allowed}")
        if start > end:
            raise ValueError("start must be on or before end")

        spec = DATASETS[dataset]
        url = f"{self.base_url}/{self.language}/datos/{spec.category}/{spec.widget}"
        resolved_time_trunc = time_trunc or spec.time_trunc
        params = {
            "start_date": start.strftime("%Y-%m-%dT%H:%M"),
            "end_date": end.strftime("%Y-%m-%dT%H:%M"),
            "time_trunc": resolved_time_trunc,
        }
        if spec.use_geo_params:
            params.update(PENINSULAR_GEO_PARAMS)

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise REDataAPIError(
                f"REData request failed for dataset={dataset}, "
                f"start={params['start_date']}, end={params['end_date']}: {exc}"
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise REDataAPIError("REData returned a non-JSON response") from exc

        if payload.get("errors"):
            raise REDataAPIError(f"REData returned an API error: {payload['errors']}")
        if "included" not in payload:
            raise REDataAPIError("REData response does not contain the expected 'included' field")
        return payload
