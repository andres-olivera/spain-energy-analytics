# Public interactive energy dashboard — deployment guide

This Streamlit app is a **companion to the actual Power BI report**, not a
replacement. The Power BI deliverable remains documented in
[dashboard/README.md](../dashboard/README.md).

## App design and data provenance

- Data originate from the public REData API, using the existing Python ETL.
- The [historical snapshot workflow](../.github/workflows/publish_energy_snapshot.yml)
  regenerates the **full year 2025** and commits a curated read-only copy in
  `app/data/`: source indicator dimension, timestamped observation values and
  metadata. No source JSON or private data are committed.
- The web app loads this committed snapshot instantly. It does not make
  dozens of public API requests whenever a recruiter opens the page.
- Filters: date range and **one explicit source indicator per dataset**.
- Pages: Overview, Demand, Generation, Market prices, About the data.

## Deploy on Streamlit Community Cloud

**First** wait until the snapshot workflow succeeds and
`app/data/source.json` exists. Without the snapshot the app deliberately
shows Power BI screenshots as a preview and labels interactive charts as
pending; it does not invent sample metrics.

1. Open https://share.streamlit.io/ using the same account as the churn app.
2. Choose **Create app** > **Deploy from GitHub**.
3. Repository: `andres-olivera/spain-energy-analytics`.
4. Branch: `main`.
5. Main file path: `app/streamlit_app.py`.
6. Public URL name, if available: `andres-spain-energy-analytics`.
7. Click **Deploy**, open the URL and exercise all report tabs and date filters.
8. Add the actual URL to the README after successful public verification.

Root `requirements.txt` installs the local project with the `app` extra.
No paid Power BI subscription is required to host this **separate Streamlit
companion app**.

## Methodological cautions

- Data represent **2025 only**. They are not live electricity prices.
- `mercados/precios-mercados-tiempo-real` is a market-price API widget.
  It must not be labeled **PVPC** without verification of the exact indicator.
- REData magnitudes are sometimes missing. Do not silently turn raw values
  into MWh or EUR/MWh.
- Demand/price observations are hourly; generation is daily.
- Never combine incompatible indicators or geographical scopes.
- The production Power BI file is not embedded within Streamlit. This demo
  implements separate, reproducible charts based on the same modeled source.

## Rebuild locally

```bash
python -m pip install -e ".[dev,app]"
python scripts/run_pipeline.py --start 2025-01-01 --end 2025-12-31 --refresh-raw
python scripts/build_public_demo.py
streamlit run app/streamlit_app.py
```
