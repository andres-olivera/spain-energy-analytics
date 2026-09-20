# Decision log

## 2026-09 â€” Initial project foundation

**Goal:** create one portfolio project that demonstrates Python, REST APIs, ETL, SQL, data modeling, data quality, GitHub CI, and a Power BI-ready semantic layer.

**Source:** Red ElÃ©ctrica de EspaÃ±a's public REData API. No API token is required for the selected endpoints.

**Model:** a shared observation fact table with indicator and date dimensions. This avoids three near-duplicate fact-table pipelines while retaining source metadata.

**Granularity:** requested as hourly by default, but minute information is retained because source widgets can evolve or return finer intervals.

**Storage:** raw JSON + processed CSV + SQLite. Raw and generated outputs are reproducible and therefore ignored by Git.

**Quality:** duplicate natural keys, null fact values, and orphan foreign keys fail the pipeline before database loading.

**Testing:** network access is excluded from automated tests; API-shaped fixtures make CI deterministic.

## 2026-09 â€” Historical demand endpoint

**Change:** the demand dataset uses `demanda/evolucion` instead of `demanda/demanda-tiempo-real`.

**Reason:** the real-time demand widget returned repeated HTTP 502 responses even for a one-day historical request. The `evolucion` widget is the REData demand-evolution view and is a better semantic fit for reproducible historical analytics.
