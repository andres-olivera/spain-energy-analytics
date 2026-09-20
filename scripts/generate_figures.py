"""Generate portfolio-ready figures from the modeled SQLite database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import StrMethodFormatter

GENERATION_LABELS = {
    "Eólica": "Wind",
    "Nuclear": "Nuclear",
    "Solar fotovoltaica": "Solar PV",
    "Ciclo combinado": "Combined cycle",
    "Hidráulica": "Hydro",
    "Cogeneración": "Cogeneration",
    "Otras renovables": "Other renewables",
    "Solar térmica": "Solar thermal",
    "Carbón": "Coal",
    "Residuos renovables": "Renewable waste",
    "Residuos no renovables": "Non-renewable waste",
}


def _year_label(connection: sqlite3.Connection) -> str:
    row = connection.execute(
        """
        SELECT MIN(d.year), MAX(d.year)
        FROM fact_observation f
        JOIN dim_date d USING (date_key)
        """
    ).fetchone()
    if not row or row[0] is None:
        return ""
    if row[0] == row[1]:
        return str(row[0])
    return f"{row[0]}–{row[1]}"


def _save_demand_profile(
    connection: sqlite3.Connection, output_dir: Path, year_label: str
) -> None:
    frame = pd.read_sql_query(
        """
        SELECT f.hour_local, AVG(f.value) AS average_value
        FROM fact_observation f
        JOIN dim_indicator i USING (indicator_key)
        WHERE i.dataset = 'demand'
        GROUP BY f.hour_local
        ORDER BY f.hour_local
        """,
        connection,
    )
    if frame.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.plot(frame["hour_local"], frame["average_value"], marker="o", markersize=4)
    ax.set_title(f"Average hourly electricity demand — Spain, {year_label}")
    ax.set_xlabel("Local hour")
    ax.set_ylabel("Average hourly demand (MWh)")
    ax.set_xticks(range(0, 24, 2))
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "demand_hourly_profile.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def _save_weekday_weekend_demand(
    connection: sqlite3.Connection, output_dir: Path, year_label: str
) -> None:
    frame = pd.read_sql_query(
        """
        SELECT
            d.is_weekend,
            AVG(f.value) AS average_value
        FROM fact_observation f
        JOIN dim_indicator i USING (indicator_key)
        JOIN dim_date d USING (date_key)
        WHERE i.dataset = 'demand'
        GROUP BY d.is_weekend
        ORDER BY d.is_weekend
        """,
        connection,
    )
    if len(frame) != 2:
        return

    labels = ["Weekday", "Weekend"]
    values = frame["average_value"].tolist()
    weekday, weekend = values
    difference = (weekday / weekend - 1) * 100 if weekend else 0

    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    bars = ax.bar(labels, values)
    ax.set_title(f"Weekday vs weekend electricity demand — Spain, {year_label}")
    ax.set_ylabel("Average hourly demand (MWh)")
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.grid(axis="y", alpha=0.25)

    for bar, value in zip(bars, values, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:,.0f}",
            ha="center",
            va="bottom",
        )

    ax.text(
        0.5,
        0.94,
        f"Weekday demand is {difference:.1f}% higher on average",
        transform=ax.transAxes,
        ha="center",
        va="top",
    )
    fig.tight_layout()
    fig.savefig(
        output_dir / "weekday_vs_weekend_demand.png",
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(fig)


def _save_generation_ranking(
    connection: sqlite3.Connection, output_dir: Path, year_label: str
) -> None:
    frame = pd.read_sql_query(
        """
        SELECT
            i.indicator_title,
            AVG(f.value) AS average_value,
            COUNT(*) AS observations
        FROM fact_observation f
        JOIN dim_indicator i USING (indicator_key)
        WHERE
            i.dataset = 'generation'
            AND i.indicator_title <> 'Generación total'
        GROUP BY i.indicator_title
        HAVING COUNT(*) >= 300
        ORDER BY average_value DESC
        """,
        connection,
    )
    if frame.empty:
        return

    frame["display_title"] = frame["indicator_title"].map(GENERATION_LABELS).fillna(
        frame["indicator_title"]
    )
    frame = frame.head(10).sort_values("average_value")

    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.barh(frame["display_title"], frame["average_value"])
    ax.set_title(f"Average daily generation by technology — Spain, {year_label}")
    ax.set_xlabel("Average daily generation (MWh)")
    ax.set_ylabel("")
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.grid(axis="x", alpha=0.2)
    ax.text(
        0,
        -0.13,
        "Stable indicators only (≥300 daily observations); total generation excluded.",
        transform=ax.transAxes,
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(output_dir / "generation_ranking.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def _save_monthly_prices(
    connection: sqlite3.Connection, output_dir: Path, year_label: str
) -> None:
    frame = pd.read_sql_query(
        """
        SELECT
            d.year,
            d.month,
            AVG(f.value) AS average_value
        FROM fact_observation f
        JOIN dim_indicator i USING (indicator_key)
        JOIN dim_date d USING (date_key)
        WHERE i.dataset = 'price'
        GROUP BY d.year, d.month
        ORDER BY d.year, d.month
        """,
        connection,
    )
    if frame.empty:
        return

    frame["period"] = pd.to_datetime(
        dict(year=frame["year"], month=frame["month"], day=1)
    )

    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.plot(frame["period"], frame["average_value"], marker="o", markersize=5)
    ax.set_title(f"Monthly average PVPC — Spain, {year_label}")
    ax.set_xlabel("Month")
    ax.set_ylabel("Average PVPC (€/MWh)")
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="x", rotation=0)
    fig.tight_layout()
    fig.savefig(output_dir / "monthly_prices.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    db_path = root / "data" / "processed" / "spain_energy.db"
    if not db_path.exists():
        raise SystemExit("Database not found. Run scripts/run_pipeline.py first.")

    output_dir = root / "docs" / "assets"
    output_dir.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    try:
        year_label = _year_label(connection)
        _save_demand_profile(connection, output_dir, year_label)
        _save_weekday_weekend_demand(connection, output_dir, year_label)
        _save_generation_ranking(connection, output_dir, year_label)
        _save_monthly_prices(connection, output_dir, year_label)
    finally:
        connection.close()

    print(f"Portfolio figures written to {output_dir}")


if __name__ == "__main__":
    main()
