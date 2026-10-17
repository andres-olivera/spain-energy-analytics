# Spain Energy Analytics — case study for hiring managers

**[Explore the public Streamlit energy dashboard](https://andres-spain-energy-analytics.streamlit.app/)**

This is a web-accessible interactive **companion** to the four-page Power BI
report, not a public Power BI embedding. The live Overview view has been
visually checked, and the owner confirmed Demand, Generation, Market prices
and date-range filtering operate without errors (17 October 2026).

## The problem (20-second introduction)

Spanish electricity operations generate hourly demand and price observations,
plus daily generation series. I wanted to demonstrate how to turn public API
data into an auditable analytical model and a dashboard a BI stakeholder could
inspect without manually cleaning each monthly response.

## What I built

- A Python data collection layer using the public REData REST API.
- Reproducible, monthly extraction with retries and source preservation.
- Data quality gates and a star-style model (fact and date/indicator dimensions).
- SQL analytics on SQLite, including window-function examples and date-aware
  comparisons of demand and prices.
- A four-page Power BI dashboard showing demand, generation and prices.
- A public Streamlit companion built on a versioned, verified 2025 REData snapshot
  with historical filters and interactive analytical charts.
- Unit/integration tests with automated CI on Python 3.11 and 3.12.

## Evidence

- A verified full-year 2025 run: 22,069 records over 365 days.
- 8,760 hourly demand readings, 8,760 price readings, 4,549 daily generation
  readings.
- [Source code and test suite](../src), [advanced SQL examples](../sql/advanced_analysis.sql),
  [Power BI overview](../dashboard/README.md), [business questions](EXECUTIVE_INSIGHTS.md).

## What I would explain in an interview

**Engineering:** Why use monthly API ingestion, raw snapshots and data quality
checks rather than importing arbitrary CSVs directly into Power BI?

**Modeling:** Why a fact/dimension model instead of flat tables?
How does one-to-many filtering from date and indicator dimensions work?

**Analytics:** Explain how `LAG`, `ROW_NUMBER` and partitioned
window averages support price-change and anomaly analysis.

**Data judgment:** Local versus UTC handling at daylight saving transitions;
never combine indicators with incompatible units.

**Business thinking:** A report is a decision aid. It can inform attention
to unusual price/demand periods but does not itself establish cost savings.

## Accurate CV bullets (English)

- Built an end-to-end Python ETL pipeline using the Spanish electricity
  operator's REST API; processed **22,069 observations** covering the full
  2025 calendar year.
- Designed a dimensional analytics model and SQLite SQL queries, including
  window functions, with automated data-quality tests and GitHub Actions CI.
- Developed a documented four-page Power BI report for demand, generation and
  market-price exploration.

## What is not yet included

Interactive public Power BI access, production database hosting, or quantified
causal savings. All four Power BI page screenshots, including the authentic
Generation capture, are now included in the dashboard documentation.
