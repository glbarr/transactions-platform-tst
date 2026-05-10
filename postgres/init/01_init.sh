#!/bin/bash
set -euo pipefail

echo ">>> Creating Airflow and Platform databases..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
    -- Airflow user + database
    CREATE USER ${AIRFLOW_DB_USER} WITH PASSWORD '${AIRFLOW_DB_PASSWORD}';
    CREATE DATABASE ${AIRFLOW_DB_NAME} OWNER ${AIRFLOW_DB_USER};

    -- Platform user + database
    CREATE USER ${PLATFORM_DB_USER} WITH PASSWORD '${PLATFORM_DB_PASSWORD}';
    CREATE DATABASE ${PLATFORM_DB_NAME} OWNER ${PLATFORM_DB_USER};
EOSQL

echo ">>> Creating schemas in platform_db..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${PLATFORM_DB_NAME}" <<-EOSQL
    CREATE SCHEMA IF NOT EXISTS raw         AUTHORIZATION ${PLATFORM_DB_USER};
    CREATE SCHEMA IF NOT EXISTS staging     AUTHORIZATION ${PLATFORM_DB_USER};
    CREATE SCHEMA IF NOT EXISTS transformed AUTHORIZATION ${PLATFORM_DB_USER};
EOSQL

echo ">>> Done."