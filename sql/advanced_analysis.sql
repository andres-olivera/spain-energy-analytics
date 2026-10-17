-- Advanced SQLite analytics for the REData star schema (2025 portfolio).
-- Every query preserves indicator_key to avoid mixing incompatible measures.
-- REData does not consistently provide magnitude metadata: do not assume units.
-- READ-ONLY. SQLite >=3.25 supports the following window functions.

-- QUERY: monthly_price_change
-- Month-on-month percentage movement per original price indicator.
WITH monthly_price AS (
    SELECT
        f.indicator_key,
        i.indicator_title,
        substr(f.date_key, 1, 7) AS month,
        AVG(f.value) AS mean_observed_price
    FROM fact_observation AS f
    JOIN dim_indicator AS i USING (indicator_key)
    WHERE i.dataset = 'price'
    GROUP BY f.indicator_key, i.indicator_title, substr(f.date_key, 1, 7)
),
lagged AS (
    SELECT
        indicator_title,
        month,
        ROUND(mean_observed_price, 3) AS mean_observed_price,
        LAG(mean_observed_price) OVER (
            PARTITION BY indicator_key ORDER BY month
        ) AS previous_month_price,
        mean_observed_price
    FROM monthly_price
)
SELECT
    indicator_title,
    month,
    mean_observed_price,
    ROUND(previous_month_price, 3) AS previous_month_price,
    ROUND(
        100.0 * (mean_observed_price - previous_month_price)
        / NULLIF(previous_month_price, 0),
        2
    ) AS change_percent
FROM lagged
ORDER BY indicator_title, month;

-- QUERY: rolling_demand
-- 7 x 24 observed-hour rolling mean for each demand indicator.
-- Window counts source observations, not necessarily exactly seven wall-clock
-- days if the original source has gaps or daylight-saving transitions.
WITH ordered AS (
    SELECT
        i.indicator_title,
        f.indicator_key,
        f.timestamp_utc,
        f.value,
        ROW_NUMBER() OVER (
            PARTITION BY f.indicator_key ORDER BY f.timestamp_utc
        ) AS observation_sequence,
        AVG(f.value) OVER (
            PARTITION BY f.indicator_key
            ORDER BY f.timestamp_utc
            ROWS BETWEEN 167 PRECEDING AND CURRENT ROW
        ) AS rolling_mean_168_observations
    FROM fact_observation AS f
    JOIN dim_indicator AS i USING (indicator_key)
    WHERE i.dataset = 'demand'
)
SELECT
    indicator_title, timestamp_utc, value,
    ROUND(rolling_mean_168_observations, 2) AS rolling_mean_168_observations
FROM ordered
WHERE observation_sequence >= 168
ORDER BY indicator_title, timestamp_utc;

-- QUERY: demand_weekday_contrast
-- Hour-by-hour weekday versus weekend mean per demand indicator.
WITH hourly AS (
    SELECT
        i.indicator_title,
        f.indicator_key,
        f.hour_local,
        d.is_weekend,
        AVG(f.value) AS mean_value,
        COUNT(*) AS observed_hours
    FROM fact_observation AS f
    JOIN dim_indicator AS i USING (indicator_key)
    JOIN dim_date AS d USING (date_key)
    WHERE i.dataset = 'demand'
    GROUP BY f.indicator_key, i.indicator_title, f.hour_local, d.is_weekend
),
pivoted AS (
    SELECT indicator_key, indicator_title, hour_local,
        MAX(CASE WHEN is_weekend = 0 THEN mean_value END) AS weekday_mean,
        MAX(CASE WHEN is_weekend = 1 THEN mean_value END) AS weekend_mean,
        MAX(CASE WHEN is_weekend = 0 THEN observed_hours END) AS weekday_n,
        MAX(CASE WHEN is_weekend = 1 THEN observed_hours END) AS weekend_n
    FROM hourly
    GROUP BY indicator_key, indicator_title, hour_local
)
SELECT indicator_title, hour_local,
    ROUND(weekday_mean, 2) AS weekday_mean,
    ROUND(weekend_mean, 2) AS weekend_mean,
    ROUND(100.0 * (weekday_mean - weekend_mean)
          / NULLIF(weekend_mean, 0), 2) AS weekday_premium_pct,
    weekday_n, weekend_n
FROM pivoted
ORDER BY indicator_title, hour_local;

-- QUERY: monthly_extreme_price_hours
-- The three largest hourly values per month per price indicator.
WITH ranked AS (
    SELECT
        i.indicator_title,
        f.indicator_key,
        substr(f.date_key, 1, 7) AS month,
        f.timestamp_utc,
        f.value,
        ROW_NUMBER() OVER (
            PARTITION BY f.indicator_key, substr(f.date_key, 1, 7)
            ORDER BY f.value DESC, f.timestamp_utc ASC
        ) AS position_in_month
    FROM fact_observation AS f
    JOIN dim_indicator AS i USING (indicator_key)
    WHERE i.dataset = 'price'
)
SELECT indicator_title, month, timestamp_utc,
    ROUND(value, 2) AS observed_price, position_in_month
FROM ranked
WHERE position_in_month <= 3
ORDER BY indicator_title, month, position_in_month;

-- QUERY: monthly_generation_rank
-- Top generation indicators in each month; never combine different magnitudes.
WITH monthly AS (
    SELECT
        i.indicator_key,
        i.indicator_title,
        i.magnitude,
        substr(f.date_key, 1, 7) AS month,
        AVG(f.value) AS avg_daily_value,
        COUNT(*) AS observation_count
    FROM fact_observation AS f
    JOIN dim_indicator AS i USING (indicator_key)
    WHERE i.dataset = 'generation'
    GROUP BY i.indicator_key, i.indicator_title, i.magnitude,
        substr(f.date_key, 1, 7)
),
ranked AS (
    SELECT *,
        DENSE_RANK() OVER (
            PARTITION BY month, magnitude ORDER BY avg_daily_value DESC
        ) AS rank_within_month
    FROM monthly
)
SELECT month, indicator_title, magnitude,
    ROUND(avg_daily_value, 2) AS avg_daily_value,
    observation_count, rank_within_month
FROM ranked
WHERE rank_within_month <= 5
ORDER BY month, magnitude, rank_within_month, indicator_title;
