import json
from datetime import date
from pathlib import Path

from spain_energy_analytics.pipeline import run_pipeline

FIXTURE = Path(__file__).parent / "fixtures" / "ree_sample_payload.json"
SOURCE_SCHEMA = Path(__file__).parents[1] / "sql" / "schema.sql"


class FixtureClient:
    def __init__(self) -> None:
        self.payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.calls = []

    def fetch(self, dataset, start, end, time_trunc="hour"):
        self.calls.append((dataset, start, end, time_trunc))
        return self.payload


def test_pipeline_writes_csv_database_and_quality_report(tmp_path: Path) -> None:
    (tmp_path / "sql").mkdir()
    (tmp_path / "sql" / "schema.sql").write_text(
        SOURCE_SCHEMA.read_text(encoding="utf-8"), encoding="utf-8"
    )
    client = FixtureClient()

    result = run_pipeline(
        start=date(2026, 1, 1),
        end=date(2026, 1, 2),
        datasets=["generation"],
        project_root=tmp_path,
        client=client,
    )

    assert result.indicator_rows == 2
    assert result.observation_rows == 4
    assert result.database_path.exists()
    assert (tmp_path / "data" / "processed" / "dim_indicator.csv").exists()
    assert (tmp_path / "data" / "processed" / "fact_observation.csv").exists()
    assert (tmp_path / "reports" / "data_quality.json").exists()
    assert len(client.calls) == 1
