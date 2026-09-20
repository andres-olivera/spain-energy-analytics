# Data dictionary

The processed layer follows a compact star-style model designed for SQL and Power BI.

## `dim_indicator`

| Column | Meaning |
|---|---|
| `indicator_key` | Stable project key: `<dataset>:<source indicator id>`. |
| `dataset` | `generation`, `demand`, or `price`. |
| `indicator_id` | Indicator ID returned by REData. |
| `indicator_title` | Human-readable REData series name. |
| `magnitude` | Source magnitude/unit category returned by REData. |
| `color` | Source display color, retained as metadata only. |
| `source_type` | Indicator type reported by REData. |
| `source_last_update` | Last-update timestamp reported by the source. |

## `dim_date`

One row per local calendar date present in the fact table. It contains year, quarter, month, ISO week, weekday name, and a weekend flag.

## `fact_observation`

| Column | Meaning |
|---|---|
| `indicator_key` | Foreign key to `dim_indicator`. |
| `timestamp_local` | Original timestamp exactly as returned by REData. |
| `timestamp_utc` | The same instant normalized to UTC. |
| `date_key` | Local calendar date, foreign key to `dim_date`. |
| `hour_local` | Local clock hour from the source timestamp. |
| `minute_local` | Local clock minute. Useful because some series may not be hourly. |
| `value` | Numeric source value. Interpret together with `magnitude` and indicator title. |
| `percentage` | Source percentage when available; otherwise null. |

## Important modeling choice

The project intentionally does **not** rename every source value to `MW`, `MWh`, or `EUR/MWh`. REData widgets can expose different magnitudes, and market granularity can evolve. Keeping a generic fact value plus source metadata prevents silent unit assumptions.
