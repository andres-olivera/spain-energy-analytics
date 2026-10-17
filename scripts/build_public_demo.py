"""Package the verified 2025 REData ETL outputs for the Streamlit portfolio app."""
from __future__ import annotations

import json
from pathlib import Path

from spain_energy_analytics.public_demo import publish_snapshot


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    result = publish_snapshot(
        processed_dir=root / "data" / "processed",
        output_dir=root / "app" / "data",
        year=2025,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
