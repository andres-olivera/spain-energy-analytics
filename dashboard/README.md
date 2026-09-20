# Power BI build guide

The pipeline writes three import-ready files to `data/processed/`:

- `fact_observation.csv`
- `dim_indicator.csv`
- `dim_date.csv`

## Model

Create these relationships in Power BI:

1. `dim_indicator[indicator_key]` **1 -> many** `fact_observation[indicator_key]`
2. `dim_date[date_key]` **1 -> many** `fact_observation[date_key]`

Use single-direction filtering from each dimension to the fact table. Mark `dim_date[date]` as the date table.

## Core measures

```DAX
Observations = COUNTROWS(fact_observation)

Average Value = AVERAGE(fact_observation[value])

Maximum Value = MAX(fact_observation[value])

Minimum Value = MIN(fact_observation[value])
```

Do not sum unlike indicators blindly. Filter by `dataset`, `indicator_title`, and `magnitude` so each visual has a well-defined unit.

## Suggested report pages

### 1. Overview
- Dataset coverage cards
- Date-range cards
- Observation count
- Slicers for dataset, indicator, year, and month

### 2. Demand
- Line chart: local timestamp vs value
- Column chart: average value by local hour
- Weekday/weekend comparison
- Indicator slicer for real, scheduled, or forecast demand series

### 3. Generation
- Technology/indicator ranking by average value
- Time series for selected technologies
- Source percentage over time when the API provides it

### 4. Prices
- Price time series
- Monthly min/average/max
- Distribution by hour
- Top and bottom price observations

## Portfolio finish

Export two clean screenshots to `dashboard/screenshots/` and add them to the main README after the report is finished. Keep the `.pbix` locally if it becomes too large for normal Git; Git LFS is an option if you want the file versioned.
