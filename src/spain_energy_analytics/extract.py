"""Raw-data extraction from REData."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .api import REDataClient, month_windows


def extract_dataset(
    client: REDataClient,
    dataset: str,
    start: date,
    end: date,
    raw_dir: Path,
    time_trunc: str = "hour",
    refresh: bool = False,
) -> list[Path]:
    """Download monthly chunks and persist the untouched JSON responses."""

    dataset_dir = raw_dir / dataset
    dataset_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for chunk_start, chunk_end in month_windows(start, end):
        filename = (
            f"{dataset}_{chunk_start:%Y-%m-%d}_{chunk_end:%Y-%m-%d}_{time_trunc}.json"
        )
        path = dataset_dir / filename
        if path.exists() and not refresh:
            written.append(path)
            continue

        payload = client.fetch(dataset, chunk_start, chunk_end, time_trunc=time_trunc)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        written.append(path)

    return written
