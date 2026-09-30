-- Required for controls operating against an existing database.
-- These fail if legacy duplicates exist; review duplicates before applying.
CREATE UNIQUE INDEX IF NOT EXISTS users_email_lower_unique
ON users (LOWER(email));

CREATE UNIQUE INDEX IF NOT EXISTS dashboard_chart_settings_dashboard_default_unique
ON dashboard_chart_settings (dashboard_id) WHERE chart_id IS NULL;
