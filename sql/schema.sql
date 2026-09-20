PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dim_indicator (
    indicator_key TEXT PRIMARY KEY,
    dataset TEXT NOT NULL,
    indicator_id TEXT NOT NULL,
    indicator_title TEXT NOT NULL,
    magnitude TEXT,
    color TEXT,
    source_type TEXT,
    source_last_update TEXT
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    day INTEGER NOT NULL,
    day_name TEXT NOT NULL,
    iso_week INTEGER NOT NULL,
    is_weekend INTEGER NOT NULL CHECK (is_weekend IN (0, 1))
);

CREATE TABLE IF NOT EXISTS fact_observation (
    indicator_key TEXT NOT NULL,
    timestamp_local TEXT NOT NULL,
    timestamp_utc TEXT NOT NULL,
    date_key TEXT NOT NULL,
    hour_local INTEGER NOT NULL CHECK (hour_local BETWEEN 0 AND 23),
    minute_local INTEGER NOT NULL CHECK (minute_local BETWEEN 0 AND 59),
    value REAL NOT NULL,
    percentage REAL,
    PRIMARY KEY (indicator_key, timestamp_local),
    FOREIGN KEY (indicator_key) REFERENCES dim_indicator(indicator_key),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

CREATE INDEX IF NOT EXISTS idx_indicator_dataset
    ON dim_indicator(dataset);
CREATE INDEX IF NOT EXISTS idx_fact_date
    ON fact_observation(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_timestamp_utc
    ON fact_observation(timestamp_utc);
