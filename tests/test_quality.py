import json
from pathlib import Path

import pytest

from spain_energy_analytics.quality import DataQualityError, run_quality_checks
from spain_energy_analytics.transform import build_date_dimension, normalize_payload

FIXTURE = Path(__file__).parent / "fixtures" / "ree_sample_payload.json"


def _tables():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    indicators, facts = normalize_payload(payload, "generation")
    dates = build_date_dimension(facts)
    return indicators, dates, facts


def test_quality_checks_pass_for_valid_tables() -> None:
    indicators, dates, facts = _tables()
    report = run_quality_checks(indicators, dates, facts)

    assert report.observation_rows == 4
    assert report.duplicate_observations == 0
    assert report.orphan_indicators == 0


def test_quality_checks_reject_duplicate_fact_key() -> None:
    indicators, dates, facts = _tables()
    duplicated = facts._append(facts.iloc[0], ignore_index=True)

    with pytest.raises(DataQualityError):
        run_quality_checks(indicators, dates, duplicated)
