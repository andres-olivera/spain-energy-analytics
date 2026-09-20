-- Portfolio SQL analysis for Spain Energy Analytics.
-- The generic `value` field keeps the original REData magnitude in dim_indicator.
-- Check `magnitude` before interpreting or aggregating values across indicators.

-- 1) Data coverage by dataset
SELECT
    i.dataset,
    COUNT(*) AS observations,
    MIN(f.timestamp_local) AS first_timestamp,
    MAX(f.timestamp_local) AS last_timestamp
FROM fact_observation AS f
JOIN dim_indicator AS i USING (indicator_key)
GROUP BY i.dataset
ORDER BY i.dataset;

-- 2) Available indicators and units/magnitudes
SELECT
    dataset,
    indicator_title,
    magnitude,
    source_last_update
FROM dim_indicator
ORDER BY dataset, indicator_title;

-- 3) Average generation value by technology/indicator
SELECT
    i.indicator_title,
    i.magnitude,
    ROUND(AVG(f.value), 2) AS average_value,
    ROUND(MAX(f.value), 2) AS maximum_value,
    COUNT(*) AS observations
FROM fact_observation AS f
JOIN dim_indicator AS i USING (indicator_key)
WHERE i.dataset = 'generation'
GROUP BY i.indicator_title, i.magnitude
ORDER BY average_value DESC;

-- 4) Demand profile by hour of day
SELECT
    i.indicator_title,
    f.hour_local,
    ROUND(AVG(f.value), 2) AS average_value
FROM fact_observation AS f
JOIN dim_indicator AS i USING (indicator_key)
WHERE i.dataset = 'demand'
GROUP BY i.indicator_title, f.hour_local
ORDER BY i.indicator_title, f.hour_local;

-- 5) Weekday vs weekend demand
SELECT
    i.indicator_title,
    CASE d.is_weekend WHEN 1 THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    ROUND(AVG(f.value), 2) AS average_value
FROM fact_observation AS f
JOIN dim_indicator AS i USING (indicator_key)
JOIN dim_date AS d USING (date_key)
WHERE i.dataset = 'demand'
GROUP BY i.indicator_title, d.is_weekend
ORDER BY i.indicator_title, d.is_weekend;

-- 6) Monthly price statistics
SELECT
    d.year,
    d.month,
    i.indicator_title,
    ROUND(AVG(f.value), 2) AS average_price,
    ROUND(MIN(f.value), 2) AS minimum_price,
    ROUND(MAX(f.value), 2) AS maximum_price
FROM fact_observation AS f
JOIN dim_indicator AS i USING (indicator_key)
JOIN dim_date AS d USING (date_key)
WHERE i.dataset = 'price'
GROUP BY d.year, d.month, i.indicator_title
ORDER BY d.year, d.month, i.indicator_title;

-- 7) Extreme price observations
SELECT
    i.indicator_title,
    f.timestamp_local,
    f.value,
    i.magnitude
FROM fact_observation AS f
JOIN dim_indicator AS i USING (indicator_key)
WHERE i.dataset = 'price'
ORDER BY f.value DESC
LIMIT 20;

-- 8) Observation completeness by month
SELECT
    i.dataset,
    d.year,
    d.month,
    COUNT(*) AS observations
FROM fact_observation AS f
JOIN dim_indicator AS i USING (indicator_key)
JOIN dim_date AS d USING (date_key)
GROUP BY i.dataset, d.year, d.month
ORDER BY i.dataset, d.year, d.month;
