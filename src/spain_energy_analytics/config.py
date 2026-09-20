"""Project configuration and REData dataset definitions."""

from __future__ import annotations

from dataclasses import dataclass

BASE_URL = "https://apidatos.ree.es"


@dataclass(frozen=True)
class DatasetSpec:
    """Metadata required to call one REData widget."""

    category: str
    widget: str
    time_trunc: str
    use_geo_params: bool = True


DATASETS: dict[str, DatasetSpec] = {
    "generation": DatasetSpec("generacion", "estructura-generacion", "day"),
    "demand": DatasetSpec("demanda", "evolucion", "hour"),
    "price": DatasetSpec("mercados", "precios-mercados-tiempo-real", "hour"),
}

# REData's peninsular system identifier. Keeping it centralized makes it easy to
# change if the API evolves.
PENINSULAR_GEO_PARAMS = {
    "geo_trunc": "electric_system",
    "geo_limit": "peninsular",
    "geo_ids": "8741",
}

DEFAULT_LANGUAGE = "es"
DEFAULT_TIMEOUT_SECONDS = 30
