"""Transform REData JSON responses into analytics-friendly tables."""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd

INDICATOR_COLUMNS = [
    "indicator_key",
    "dataset",
    "indicator_id",
    "indicator_title",
    "magnitude",
    "color",
    "source_type",
    "source_last_update",
]

FACT_COLUMNS = [
    "indicator_key",
    "timestamp_local",
    "timestamp_utc",
    "date_key",
    "hour_local",
    "minute_local",
    "value",
    "percentage",
]


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-") or "unknown"


def _parse_local_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def normalize_payload(payload: dict, dataset: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Normalize one REData response into indicator and observation tables."""

    indicator_rows: list[dict] = []
    fact_rows: list[dict] = []

    for entry in payload.get("included", []):
        attrs = entry.get("attributes") or {}
        title = str(attrs.get("title") or entry.get("type") or "Unknown")
        indicator_id = str(entry.get("id") or _slug(title))
        key = f"{dataset}:{indicator_id}"

        indicator_rows.append(
            {
                "indicator_key": key,
                "dataset": dataset,
                "indicator_id": indicator_id,
                "indicator_title": title,
                "magnitude": attrs.get("magnitude"),
                "color": attrs.get("color"),
                "source_type": attrs.get("type") or entry.get("type"),
                "source_last_update": attrs.get("last-update"),
            }
        )

        for observation in attrs.get("values") or []:
            timestamp_local = observation.get("datetime")
            if timestamp_local is None or observation.get("value") is None:
                continue

            local_dt = _parse_local_timestamp(str(timestamp_local))
            utc_dt = pd.to_datetime(timestamp_local, utc=True)
            fact_rows.append(
                {
                    "indicator_key": key,
                    "timestamp_local": str(timestamp_local),
                    "timestamp_utc": utc_dt.isoformat().replace("+00:00", "Z"),
                    "date_key": local_dt.date().isoformat(),
                    "hour_local": local_dt.hour,
                    "minute_local": local_dt.minute,
                    "value": float(observation["value"]),
                    "percentage": (
                        float(observation["percentage"])
                        if observation.get("percentage") is not None
                        else None
                    ),
                }
            )

    indicators = pd.DataFrame(indicator_rows, columns=INDICATOR_COLUMNS)
    observations = pd.DataFrame(fact_rows, columns=FACT_COLUMNS)

    if not indicators.empty:
        indicators = indicators.drop_duplicates(subset=["indicator_key"], keep="last")
    if not observations.empty:
        observations = observations.drop_duplicates(
            subset=["indicator_key", "timestamp_local"], keep="last"
        )

    return indicators.reset_index(drop=True), observations.reset_index(drop=True)


def transform_raw_files(
    paths_by_dataset: dict[str, list[Path]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Transform and concatenate a set of raw JSON files."""

    indicator_frames: list[pd.DataFrame] = []
    fact_frames: list[pd.DataFrame] = []

    for dataset, paths in paths_by_dataset.items():
        for path in paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            indicators, facts = normalize_payload(payload, dataset)
            indicator_frames.append(indicators)
            fact_frames.append(facts)

    indicators = (
        pd.concat(indicator_frames, ignore_index=True)
        if indicator_frames
        else pd.DataFrame(columns=INDICATOR_COLUMNS)
    )
    facts = (
        pd.concat(fact_frames, ignore_index=True)
        if fact_frames
        else pd.DataFrame(columns=FACT_COLUMNS)
    )

    if not indicators.empty:
        indicators = indicators.drop_duplicates(subset=["indicator_key"], keep="last")
        indicators = indicators.sort_values(["dataset", "indicator_title", "indicator_key"])
    if not facts.empty:
        facts = facts.drop_duplicates(
            subset=["indicator_key", "timestamp_local"], keep="last"
        )
        facts = facts.sort_values(["timestamp_utc", "indicator_key"])

    return indicators.reset_index(drop=True), facts.reset_index(drop=True)


def build_date_dimension(observations: pd.DataFrame) -> pd.DataFrame:
    """Build a reusable calendar dimension from fact-table dates."""

    columns = [
        "date_key",
        "date",
        "year",
        "quarter",
        "month",
        "month_name",
        "day",
        "day_name",
        "iso_week",
        "is_weekend",
    ]
    if observations.empty:
        return pd.DataFrame(columns=columns)

    dates = pd.to_datetime(observations["date_key"].drop_duplicates()).sort_values()
    frame = pd.DataFrame({"date": dates})
    frame["date_key"] = frame["date"].dt.strftime("%Y-%m-%d")
    frame["year"] = frame["date"].dt.year
    frame["quarter"] = frame["date"].dt.quarter
    frame["month"] = frame["date"].dt.month
    frame["month_name"] = frame["date"].dt.month_name()
    frame["day"] = frame["date"].dt.day
    frame["day_name"] = frame["date"].dt.day_name()
    frame["iso_week"] = frame["date"].dt.isocalendar().week.astype(int)
    frame["is_weekend"] = frame["date"].dt.dayofweek.ge(5).astype(int)
    frame["date"] = frame["date"].dt.strftime("%Y-%m-%d")
    return frame[columns].reset_index(drop=True)
