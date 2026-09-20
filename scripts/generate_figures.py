"""Generate portfolio figures from the modeled SQLite database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def _save_demand_profile(connection: sqlite3.Connection, output_dir: Path) -> None:
    frame = pd.read_sql_query(
        """
        SELECT i.indicator_title, f.hour_local, AVG(f.value) AS average_value
        FROM fact_observation f
        JOIN dim_indicator i USING (indicator_key)
        WHERE i.dataset = 'demand'
        GROUP BY i.indicator_title, f.hour_local
        ORDER BY i.indicator_title, f.hour_local
        """,
        connection,
    )
    if frame.empty:
        return

    pivot = frame.pivot(
        index="hour_local", columns="indicator_title", values="average_value"
    )
    ax = pivot.plot(figsize=(10, 5))
    ax.set_title("Average electricity demand profile by local hour")
    ax.set_xlabel("Local hour")
    ax.set_ylabel("Source value — inspect indicator magnitude")
    ax.figure.tight_layout()
    ax.figure.savefig(output_dir / "demand_hourly_profile.png", dpi=160)
    plt.close(ax.figure)


def _save_generation_ranking(connection: sqlite3.Connection, output_dir: Path) -> None:
    frame = pd.read_sql_query(
        """
        SELECT i.indicator_title, i.magnitude, AVG(f.value) AS average_value
        FROM fact_observation f
        JOIN dim_indicator i USING (indicator_key)
        WHERE i.dataset = 'generation'
        GROUP BY i.indicator_title, i.magnitude
        ORDER BY average_value DESC
        LIMIT 12
        """,
        connection,
    )
    if frame.empty:
        return

    frame = frame.sort_values("average_value")
    ax = frame.plot.barh(
        x="indicator_title", y="average_value", legend=False, figsize=(10, 6)
    )
    ax.set_title("Generation indicators ranked by average value")
    ax.set_xlabel("Average source value — inspect magnitude")
    ax.set_ylabel("")
    ax.figure.tight_layout()
    ax.figure.savefig(output_dir / "generation_ranking.png", dpi=160)
    plt.close(ax.figure)


def _save_monthly_prices(connection: sqlite3.Connection, output_dir: Path) -> None:
    frame = pd.read_sql_query(
        """
        SELECT d.year, d.month, i.indicator_title, AVG(f.value) AS average_value
        FROM fact_observation f
        JOIN dim_indicator i USING (indicator_key)
        JOIN dim_date d USING (date_key)
        WHERE i.dataset = 'price'
        GROUP BY d.year, d.month, i.indicator_title
        ORDER BY d.year, d.month, i.indicator_title
        """,
        connection,
    )
    if frame.empty:
        return

    frame["period"] = pd.to_datetime(
        dict(year=frame["year"], month=frame["month"], day=1)
    )
    pivot = frame.pivot(
        index="period", columns="indicator_title", values="average_value"
    )
    ax = pivot.plot(figsize=(10, 5))
    ax.set_title("Monthly average electricity price indicators")
    ax.set_xlabel("Month")
    ax.set_ylabel("Average source value — inspect magnitude")
    ax.figure.tight_layout()
    ax.figure.savefig(output_dir / "monthly_prices.png", dpi=160)
    plt.close(ax.figure)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    db_path = root / "data" / "processed" / "spain_energy.db"
    if not db_path.exists():
        raise SystemExit("Database not found. Run scripts/run_pipeline.py first.")

    output_dir = root / "reports" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    try:
        _save_demand_profile(connection, output_dir)
        _save_generation_ranking(connection, output_dir)
        _save_monthly_prices(connection, output_dir)
    finally:
        connection.close()

    print(f"Figures written to {output_dir}")


if __name__ == "__main__":
    main()
