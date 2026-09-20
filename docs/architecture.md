# Architecture and engineering decisions

```text
REData REST API
      |
      v
src/.../api.py  -- retries, timeout, monthly chunks
      |
      v
data/raw/<dataset>/*.json  -- immutable source layer (gitignored)
      |
      v
src/.../transform.py
      |
      +--> dim_indicator.csv
      +--> dim_date.csv
      +--> fact_observation.csv
      |
      v
quality checks
      |
      +--> reports/data_quality.json
      |
      v
SQLite analytical database
      |
      +--> SQL portfolio analysis
      +--> Power BI import layer
```

## Why monthly API chunks?

The pipeline requests one calendar month at a time. This makes retries smaller, raw files inspectable, reruns incremental, and behavior less dependent on endpoint-specific range limits.

## Why keep both local and UTC timestamps?

Spanish electricity data crosses daylight-saving-time transitions. The original local timestamp is useful for business interpretation, while UTC gives a stable chronological key for engineering and QA.

## Why SQLite *and* CSV?

SQLite provides a zero-setup SQL environment for portfolio queries and tests. CSV exports make the same modeled tables easy to load into Power BI. A future production deployment could replace SQLite with PostgreSQL without changing the source model.

## Why raw data is not committed

Public API responses can become large. Git stores source code and documentation; the pipeline recreates raw and processed data deterministically. This keeps the repository lightweight and avoids stale copies of third-party data.
