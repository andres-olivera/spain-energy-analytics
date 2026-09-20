from datetime import date

import pytest

from spain_energy_analytics.api import month_windows


def test_month_windows_splits_across_months() -> None:
    windows = list(month_windows(date(2025, 1, 15), date(2025, 3, 2)))

    assert len(windows) == 3
    assert windows[0][0].isoformat(timespec="minutes") == "2025-01-15T00:00"
    assert windows[0][1].isoformat(timespec="minutes") == "2025-01-31T23:59"
    assert windows[-1][0].isoformat(timespec="minutes") == "2025-03-01T00:00"
    assert windows[-1][1].isoformat(timespec="minutes") == "2025-03-02T23:59"


def test_month_windows_rejects_reversed_range() -> None:
    with pytest.raises(ValueError):
        list(month_windows(date(2025, 2, 1), date(2025, 1, 1)))
