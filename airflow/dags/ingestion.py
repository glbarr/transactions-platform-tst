"""
airflow/dags/ingestion.py

Ingests customer_transactions.csv into raw.customer_transactions in PostgreSQL.
On success, triggers the transformations DAG.
"""

import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

sys.path.insert(0, "/opt/airflow/scripts")
from ingest import ingest

default_args = {
    "owner": "data-platform",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="ingestion",
    description="Ingest customer transactions CSV into raw schema",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args=default_args,
    tags=["platform", "ingestion"],
) as dag:

    ingest_data = PythonOperator(
        task_id="ingest_data",
        python_callable=ingest,
    )

    trigger_transformations = TriggerDagRunOperator(
        task_id="trigger_transformations",
        trigger_dag_id="transformations",
        wait_for_completion=False,
    )

    ingest_data >> trigger_transformations