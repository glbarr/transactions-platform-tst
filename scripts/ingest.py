"""
ingestion/ingest.py

Loads customer_transactions.csv into raw.customer_transactions in PostgreSQL.

Design decisions:
- Raw layer is immutable source data: no casting, no cleaning, load as-is
- Idempotent: truncates and reloads on every run
- Chunked reads: avoids loading the full CSV into memory
- All type casting and cleaning happens downstream in dbt staging models
"""

import os
import logging
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DB_CONFIG = {
    "host":     os.environ["PLATFORM_DB_HOST"],
    "port":     int(os.environ.get("PLATFORM_DB_PORT", 5432)),
    "dbname":   os.environ["PLATFORM_DB_NAME"],
    "user":     os.environ["PLATFORM_DB_USER"],
    "password": os.environ["PLATFORM_DB_PASSWORD"],
}

CSV_PATH   = os.environ.get("CSV_PATH", "/data/customer_transactions.csv")
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 1000))
SCHEMA     = "raw"
TABLE      = "customer_transactions"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def create_table(cursor):
    """
    Create raw table if it doesn't exist.
    All columns are text — raw layer preserves source data exactly.
    Type casting happens in dbt staging.
    """
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA}.{TABLE} (
            transaction_id   TEXT,
            customer_id      TEXT,
            transaction_date TEXT,
            product_id       TEXT,
            product_name     TEXT,
            quantity         TEXT,
            price            TEXT,
            tax              TEXT,
            _ingested_at     TIMESTAMP DEFAULT NOW()
        );
    """)
    log.info(f"Table {SCHEMA}.{TABLE} ready.")


def truncate_table(cursor):
    cursor.execute(f"TRUNCATE TABLE {SCHEMA}.{TABLE};")
    log.info(f"Truncated {SCHEMA}.{TABLE}.")


def insert_chunk(cursor, chunk: pd.DataFrame):
    # Replace pandas NA with None so psycopg2 writes NULL
    records = chunk.where(pd.notna(chunk), None).values.tolist()
    execute_values(
        cursor,
        f"""
        INSERT INTO {SCHEMA}.{TABLE} (
            transaction_id, customer_id, transaction_date,
            product_id, product_name, quantity, price, tax
        ) VALUES %s
        """,
        records,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def ingest():
    log.info(f"Starting ingestion from {CSV_PATH}")

    conn = get_connection()
    conn.autocommit = False

    try:
        with conn.cursor() as cur:
            create_table(cur)
            truncate_table(cur)

            total_rows = 0
            for chunk in pd.read_csv(CSV_PATH, chunksize=CHUNK_SIZE, dtype=str):
                insert_chunk(cur, chunk)
                total_rows += len(chunk)
                log.info(f"Inserted {total_rows} rows so far...")

        conn.commit()
        log.info(f"Ingestion complete. Total rows: {total_rows}")

    except Exception as e:
        conn.rollback()
        log.error(f"Ingestion failed: {e}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    ingest()