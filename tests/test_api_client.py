from datetime import datetime

from spain_energy_analytics.api import REDataClient


class FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"included": []}


class FakeSession:
    def __init__(self) -> None:
        self.last_url = None
        self.last_params = None
        self.last_timeout = None

    def get(self, url, params, timeout):
        self.last_url = url
        self.last_params = params
        self.last_timeout = timeout
        return FakeResponse()


def test_client_builds_expected_redata_request() -> None:
    session = FakeSession()
    client = REDataClient(session=session, timeout=12)

    client.fetch(
        "generation",
        datetime(2025, 1, 1, 0, 0),
        datetime(2025, 1, 31, 23, 59),
    )

    assert session.last_url.endswith("/es/datos/generacion/estructura-generacion")
    assert session.last_params["start_date"] == "2025-01-01T00:00"
    assert session.last_params["end_date"] == "2025-01-31T23:59"
    assert session.last_params["time_trunc"] == "hour"
    assert session.last_params["geo_limit"] == "peninsular"
    assert session.last_params["geo_ids"] == "8741"
    assert session.last_timeout == 12
