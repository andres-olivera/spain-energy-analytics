"""Public interactive explorer built on the REData-derived portfolio snapshot.

This is a companion to (not a replacement for) the original Power BI dashboard.
All readings are historical; different indicators and magnitudes are NEVER
added together to create misleading prices, demand totals or energy shares.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "app" / "data"
st.set_page_config(page_title="Spain Energy | Analytics Explorer", page_icon="⚡", layout="wide")


@st.cache_data(show_spinner="Loading historical REData observations…")
def load_snapshot() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    dims = pd.read_csv(SNAPSHOT / "indicators.csv")
    facts = pd.read_csv(SNAPSHOT / "observations.csv")
    info = json.loads((SNAPSHOT / "source.json").read_text(encoding="utf-8"))
    if not {"indicator_key", "dataset", "indicator_title", "magnitude"} <= set(dims):
        raise ValueError("Invalid indicator dimension in published snapshot")
    if not {"indicator_key", "date_key", "hour_local", "value"} <= set(facts):
        raise ValueError("Invalid observation columns in published snapshot")
    if facts.empty or facts["indicator_key"].isna().any():
        raise ValueError("Published snapshot is incomplete")
    if not facts["indicator_key"].isin(dims["indicator_key"]).all():
        raise ValueError("Observations without source indicator metadata")
    facts["date"] = pd.to_datetime(facts["date_key"], errors="raise")
    facts["value"] = pd.to_numeric(facts["value"], errors="raise")
    merged = facts.merge(
        dims, on="indicator_key", how="left", validate="many_to_one",
    )
    return merged, dims, info


def unit_suffix(dims: pd.DataFrame, indicator_key: str) -> str:
    """Use only the original source magnitude; never invent MWh or euros."""
    found = dims.loc[dims["indicator_key"] == indicator_key, "magnitude"]
    if found.empty or pd.isna(found.iloc[0]) or not str(found.iloc[0]).strip():
        return "REData source value (unit not supplied)"
    return f"REData source value ({found.iloc[0]})"


def plot_line(frame: pd.DataFrame, x: str, y: str, title: str, label: str):
    figure = px.line(frame, x=x, y=y, markers=False, title=title)
    figure.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=55, b=15),
        xaxis_title=None,
        yaxis_title=label,
        hovermode="x unified",
    )
    st.plotly_chart(figure, use_container_width=True)


def daily_mean(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby("date", as_index=False)["value"]
        .mean().rename(columns={"value": "mean_value"})
        .sort_values("date")
    )


st.title("⚡ Spain Energy | Analytics Explorer")
st.caption("Interactive companion to Spain Energy Analytics (Power BI + Python + SQL)")
st.info(
    "Historical REData observations for 2025 — **not** real-time electricity data. "
    "The app preserves original series; it does not mix different indicators "
    "or infer missing units."
)

if not (SNAPSHOT / "source.json").exists():
    st.warning(
        "The versioned public 2025 data snapshot has not been published yet. "
        "The GitHub Actions historical-snapshot workflow must finish successfully "
        "before the interactive charts become available."
    )
    st.write("Meanwhile, the original Power BI report's screenshots are available:")
    for path, label in [
        ("overview.png", "Overview"),
        ("demand.png", "Demand"),
        ("generation.png", "Generation"),
        ("prices.png", "Prices"),
    ]:
        path_to_image = ROOT / "dashboard" / "screenshots" / path
        if path_to_image.exists():
            st.subheader(label)
            st.image(str(path_to_image), use_container_width=True)
    st.markdown(
        "[Full Power BI dashboard documentation]"
        "(https://github.com/andres-olivera/spain-energy-analytics/tree/main/dashboard)"
    )
    st.stop()

try:
    data, indicators, source = load_snapshot()
except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
    st.error(f"Could not validate the public REData snapshot: {exc}")
    st.stop()

all_dates = data["date"].dt.date
minimum, maximum = all_dates.min(), all_dates.max()
st.sidebar.header("Explore 2025")
range_value = st.sidebar.date_input(
    "Date range", value=(minimum, maximum), min_value=minimum, max_value=maximum
)
if not isinstance(range_value, (tuple, list)) or len(range_value) != 2:
    st.sidebar.info("Select both start and end dates.")
    st.stop()
start_date, end_date = range_value
if start_date > end_date:
    st.error("The start date must not be after the end date.")
    st.stop()
filtered = data.loc[
    data["date"].dt.date.between(start_date, end_date)
].copy()
st.sidebar.caption(f"Historical period: {minimum} – {maximum}")
st.sidebar.caption("Source: Red Eléctrica REData API")

# One explicit indicator per chart; this avoids mixing disparate source series.
choices = {}
for category in ("demand", "generation", "price"):
    subset = indicators.loc[indicators["dataset"] == category].copy()
    subset = subset.loc[subset["indicator_key"].isin(filtered["indicator_key"])]
    choices[category] = subset.sort_values(["indicator_title", "indicator_key"])


def choose_indicator(category: str, label: str) -> str | None:
    options = choices[category]
    if options.empty:
        return None
    keys = options["indicator_key"].tolist()
    titles = dict(zip(options["indicator_key"], options["indicator_title"], strict=True))
    return st.sidebar.selectbox(
        label, keys, format_func=lambda key: f"{titles[key]} ({key})",
    )


demand_key = choose_indicator("demand", "Demand series")
price_key = choose_indicator("price", "Market price series")
generation_key = choose_indicator("generation", "Generation series")
demand = filtered.loc[filtered["indicator_key"] == demand_key].copy()
price = filtered.loc[filtered["indicator_key"] == price_key].copy()
generation = filtered.loc[filtered["indicator_key"] == generation_key].copy()

st.subheader("2025 data coverage")
a, b, c, d = st.columns(4)
a.metric("Filtered observations", f"{len(filtered):,}")
b.metric("Observed days", f"{filtered['date'].nunique():,}")
c.metric("Source indicators", f"{filtered['indicator_key'].nunique():,}")
d.metric("Data categories", f"{filtered['dataset'].nunique():,}")

overview_tab, demand_tab, gen_tab, price_tab, method_tab = st.tabs(
    ["Overview", "Demand", "Generation", "Market prices", "About the data"]
)

with overview_tab:
    st.markdown(
        "### Explore patterns, not invented aggregate totals\n"
        "The two charts below show the average **within the selected source indicator** "
        "for each day; their vertical axes may have different magnitudes."
    )
    left, right = st.columns(2)
    with left:
        if not demand.empty:
            plot_line(
                daily_mean(demand), "date", "mean_value",
                "Daily mean — selected demand series", unit_suffix(indicators, demand_key),
            )
    with right:
        if not price.empty:
            plot_line(
                daily_mean(price), "date", "mean_value",
                "Daily mean — selected market price series",
                unit_suffix(indicators, price_key),
            )
    st.caption(
        "No source price series is identified as PVPC unless REData itself "
        "identifies it so."
    )

with demand_tab:
    st.markdown("### Demand: daily and intra-day behavior")
    if demand.empty:
        st.info("No matching demand observations.")
    else:
        plot_line(
            daily_mean(demand), "date", "mean_value", "Daily mean of selected demand indicator",
            unit_suffix(indicators, demand_key),
        )
        left, right = st.columns(2)
        with left:
            by_hour = demand.groupby("hour_local", as_index=False)["value"].mean()
            fig = px.line(
                by_hour, x="hour_local", y="value", markers=True,
                title="Average value by local hour",
                labels={"value": unit_suffix(indicators, demand_key)},
            )
            fig.update_layout(height=370, margin=dict(l=10, r=10, t=55, b=15))
            st.plotly_chart(fig, use_container_width=True)
        with right:
            tmp = demand.copy()
            tmp["Day type"] = tmp["date"].dt.dayofweek.map(
                lambda day: "Weekend" if day >= 5 else "Weekday"
            )
            by_type = tmp.groupby("Day type", as_index=False)["value"].mean()
            fig = px.bar(
                by_type, x="Day type", y="value",
                title="Weekdays vs weekends (mean source value)",
                labels={"value": unit_suffix(indicators, demand_key)},
            )
            fig.update_layout(height=370, margin=dict(l=10, r=10, t=55, b=15))
            st.plotly_chart(fig, use_container_width=True)

with gen_tab:
    st.markdown("### Generation: individual technologies")
    st.caption(
        "Daily series from REData. Rankings show an **average source value** "
        "per technology, never a sum across indicators."
    )
    if not generation.empty:
        plot_line(
            daily_mean(generation), "date", "mean_value",
            "Selected generation series over time",
            unit_suffix(indicators, generation_key),
        )
    tech = filtered.loc[filtered["dataset"] == "generation"].copy()
    tech = tech.loc[
        ~tech["indicator_title"].str.contains("generación total", case=False, na=False)
    ]
    if not tech.empty:
        rank = (
            tech.groupby(["indicator_key", "indicator_title", "magnitude"], dropna=False)
            .agg(mean_value=("value", "mean"), n=("value", "size"))
            .reset_index()
        )
        # Do not rank indicators with mixed or unknown magnitudes as if comparable.
        known = rank["magnitude"].dropna().astype(str).str.strip()
        if len(known) == len(rank) and known.nunique() == 1:
            rank = rank.nlargest(10, "mean_value").sort_values("mean_value")
            fig = px.bar(
                rank, y="indicator_title", x="mean_value", orientation="h",
                title="Average generation source value by technology (same magnitude)",
                labels={"mean_value": f"Average source value ({known.iloc[0]})",
                        "indicator_title": "Technology"},
            )
            fig.update_layout(height=460, margin=dict(l=10, r=10, t=55, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(
                "REData did not supply consistent unit metadata for technology rankings. "
                "Comparisons are withheld rather than presenting incomparable values."
            )

with price_tab:
    st.markdown("### Market prices")
    st.caption(
        "The selected indicator comes from REData's 'precios-mercados-tiempo-real' "
        "widget. This does not establish that the series represents the regulated PVPC tariff."
    )
    if price.empty:
        st.info("No matching market price observations.")
    else:
        price["month"] = price["date"].dt.to_period("M").dt.to_timestamp()
        monthly = price.groupby("month", as_index=False)["value"].mean()
        plot_line(
            monthly, "month", "value",
            "Monthly mean — selected price indicator",
            unit_suffix(indicators, price_key),
        )
        plot_line(
            daily_mean(price), "date", "mean_value",
            "Daily mean — selected price indicator",
            unit_suffix(indicators, price_key),
        )
        hourly = price.groupby("hour_local", as_index=False)["value"].mean()
        fig = px.bar(
            hourly, x="hour_local", y="value", title="Average by local hour",
            labels={"hour_local": "Local hour",
                    "value": unit_suffix(indicators, price_key)},
        )
        fig.update_layout(height=350, margin=dict(l=10, r=10, t=55, b=20))
        st.plotly_chart(fig, use_container_width=True)

with method_tab:
    st.markdown(
        "### Reproducibility and methodology\n"
        "This companion app uses the same API-derived, quality-checked "
        "fact/dimension model as the original Power BI project. "
        "The snapshot is versioned so a recruiter can open it without "
        "waiting for 36 remote API requests."
    )
    st.json(source)
    st.markdown(
        "- **Original Power BI:** "
        "[four-page dashboard](https://github.com/andres-olivera/"
        "spain-energy-analytics/tree/main/dashboard)\n"
        "- **ETL and data provenance:** "
        "[repository](https://github.com/andres-olivera/spain-energy-analytics)\n"
        "- **Data source:** [REData](https://www.ree.es/en/datos/apidata)"
    )
    st.warning(
        "Historic snapshot only; original source units may be missing. "
        "Different indicators should not be merged without validating "
        "their meaning, geography, resolution and units."
    )
