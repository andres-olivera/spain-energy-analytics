# Executive interpretation guide — Spain Energy Analytics

## What is the business problem?

Electricity demand, generation mix and consumer prices evolve on different
schedules. An operations or procurement analyst needs an auditable way to
compare their patterns, identify outliers and explain where further analysis
could inform decisions. This project builds the ingestion and modeling layer
for such analysis from REData's public historical indicators.

## Verified scope

- 2025 dataset: **22,069 observations** over **365 dates**.
- 8,760 hourly observations for demand, 8,760 for the market-price feed and
  4,549 daily generation observations.
- Four-page Power BI reporting experience plus reproducible Python figures.
- Analyzable fact/dimension schema, data-quality validation and SQLite SQL.

These are dataset coverage facts, **not** derived financial savings.

## Four questions a stakeholder could ask

1. **When is demand systematically higher?** Compare local-hour average profiles
   between weekday and weekend records and inspect how many readings support
   each result. See `demand_weekday_contrast`.
2. **Which months have the largest price changes?** Compare per-indicator
   monthly price averages with the prior month using `LAG()`. See
   `monthly_price_change`.
3. **Which hours look atypical?** Review each month's three largest hourly
   price records with `ROW_NUMBER()`; corroborate unusual readings with
   data source documentation and timezone treatment. See
   `monthly_extreme_price_hours`.
4. **How do generation rankings evolve?** Compare daily per-technology
   monthly averages, always preserving indicator and magnitude group. See
   `monthly_generation_rank`.

## Methodology and caveats

- REData source `magnitude` metadata can be null. Do **not** assign MWh or
  €/MWh to unverified readings or add incompatible units together.
- Demand/price are hourly; generation is daily. Do not join across
  resolution without an explicit aggregation rule.
- Timestamp storage includes Spanish local time and UTC to cope with DST.
- Average values are descriptive; peak periods and observed correlations
  do not establish causal drivers or implied cost reductions.

## Reproduce the analysis

```bash
python scripts/run_pipeline.py --start 2025-01-01 --end 2025-12-31 --refresh-raw
python scripts/run_advanced_sql.py
```

The advanced script exports one CSV per question to `reports/tables/`.
Actual quantified insights should be added **only after those queries have
been executed on the underlying downloaded data**, with units verified.
No revenue, profit, or percentage findings are invented in this document.

## Presentation improvements still pending

- Complete: an authentic Generation page capture is now included in
  [`dashboard/screenshots/generation.png`](../dashboard/screenshots/generation.png).
- Share a playable dashboard if your organization's Power BI publishing
  policies permit, or add an accurate narrated demonstration.
