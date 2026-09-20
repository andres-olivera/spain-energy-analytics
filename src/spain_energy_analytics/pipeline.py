"""Orchestration for the end-to-end ETL pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .api import REDataClient
from .database import load_sqlite
from .extract import extract_dataset
from .quality import run_quality_checks
from .transform import build_date_dimension, transform_raw_files


@dataclass(frozen=True)
class PipelineResult:
    indicator_rows: int
    observation_rows: int
    date_rows: int
    database_path: Path
    processed_dir: Path


def run_pipeline(
    start: date,
    end: date,
    datasets: list[str],
    project_root: Path,
    time_trunc: str = "hour",
    refresh_raw: bool = False,
    client: REDataClient | None = None,
) -> PipelineResult:
    """Extract, transform, validate, persist, and load the selected datasets."""

    if start > end:
        raise ValueError("start must be on or before end")
    if not datasets:
        raise ValueError("At least one dataset is required")

    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    reports_dir = project_root / "reports"
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    api_client = client or REDataClient()
    paths_by_dataset: dict[str, list[Path]] = {}
    for dataset in datasets:
        paths_by_dataset[dataset] = extract_dataset(
            api_client,
            dataset,
            start,
            end,
            raw_dir=raw_dir,
            time_trunc=time_trunc,
            refresh=refresh_raw,
        )

    indicators, observations = transform_raw_files(paths_by_dataset)
    if observations.empty:
        raise RuntimeError("The pipeline produced no observations")

    dates = build_date_dimension(observations)
    quality_report = run_quality_checks(indicators, dates, observations)

    indicators.to_csv(processed_dir / "dim_indicator.csv", index=False)
    dates.to_csv(processed_dir / "dim_date.csv", index=False)
    observations.to_csv(processed_dir / "fact_observation.csv", index=False)

    db_path = processed_dir / "spain_energy.db"
    load_sqlite(
        indicators,
        dates,
        observations,
        db_path=db_path,
        schema_path=project_root / "sql" / "schema.sql",
    )

    (reports_dir / "data_quality.json").write_text(
        json.dumps(quality_report.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return PipelineResult(
        indicator_rows=len(indicators),
        observation_rows=len(observations),
        date_rows=len(dates),
        database_path=db_path,
        processed_dir=processed_dir,
    )
