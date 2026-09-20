# Decision log

## 2026-09 — Initial project foundation

**Goal:** create one portfolio project that demonstrates Python, REST APIs, ETL, SQL, data modeling, data quality, GitHub CI, and a Power BI-ready semantic layer.

**Source:** Red Eléctrica de España's public REData API. No API token is required for the selected endpoints.

**Model:** a shared observation fact table with indicator and date dimensions. This avoids three near-duplicate fact-table pipelines while retaining source metadata.

**Granularity:** requested as hourly by default, but minute information is retained because source widgets can evolve or return finer intervals.

**Storage:** raw JSON + processed CSV + SQLite. Raw and generated outputs are reproducible and therefore ignored by Git.

**Quality:** duplicate natural keys, null fact values, and orphan foreign keys fail the pipeline before database loading.

**Testing:** network access is excluded from automated tests; API-shaped fixtures make CI deterministic.

## 2026-09 — Historical demand endpoint

**Change:** the demand dataset uses `demanda/evolucion` instead of `demanda/demanda-tiempo-real`.

**Reason:** the real-time demand widget returned repeated HTTP 502 responses even for a one-day historical request. The `evolucion` widget is the REData demand-evolution view and is a better semantic fit for reproducible historical analytics.


## 2026-09 — Dataset-specific source resolution

**Change:** each dataset owns its validated REData aggregation: demand is hourly, price is hourly, and generation is daily.

**Reason:** live API validation showed that `generacion/estructura-generacion` rejects `time_trunc=hour` with HTTP 400 but succeeds with `time_trunc=day`. Demand and price both succeeded at hourly resolution. Keeping this metadata in configuration prevents invalid cross-dataset assumptions while preserving a single reusable pipeline.

## 2026-09 — Portfolio visualization layer

**Validated run:** the complete 2025 extraction produced 22,069 modeled observations across 365 dates: 8,760 demand, 8,760 PVPC-price, and 4,549 generation observations.

**Generation coverage:** 12 generation indicators provide full-year daily coverage. `Turbina de vapor` appears for 168 days and `Fuel + Gas` for one day; these source-taxonomy changes are retained in the model but excluded from the stable-technology ranking visual.

**Units:** REData's `magnitude` field is not consistently populated in these live responses. The analytical model preserves that null metadata instead of fabricating it. Portfolio visual labels use Red Eléctrica's published public-data conventions (MWh for demand/generation energy and €/MWh for PVPC presentation), and this distinction is documented explicitly.

**Presentation:** static figures are generated from SQLite into `docs/assets/` so GitHub renders useful project outputs without committing reproducible raw datasets or the local database.
