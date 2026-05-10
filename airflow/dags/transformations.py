"""
airflow/dags/transformations.py

Runs dbt models and tests against raw.customer_transactions.
Triggered by the ingestion DAG on success.
"""

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

default_args = {
    "owner": "data-platform",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

DBT_IMAGE = os.environ.get("DBT_IMAGE", "ebury/dbt:1.9.0")

DBT_ENVIRONMENT = {
    "PLATFORM_DB_HOST":     os.environ.get("PLATFORM_DB_HOST", "postgres"),
    "PLATFORM_DB_NAME":     os.environ.get("PLATFORM_DB_NAME"),
    "PLATFORM_DB_USER":     os.environ.get("PLATFORM_DB_USER"),
    "PLATFORM_DB_PASSWORD": os.environ.get("PLATFORM_DB_PASSWORD"),
}

DBT_MOUNTS = [
    Mount(
        source="/Users/gabriel/Documents/transactions-platform-tst-1/dbt",
        target="/dbt",
        type="bind",
    )
]

DOCKER_KWARGS = {
    "image": DBT_IMAGE,
    "environment": DBT_ENVIRONMENT,
    "mounts": DBT_MOUNTS,
    "network_mode": os.environ.get("DOCKER_NETWORK", "transactions-platform-tst-1_platform_net"),
    "auto_remove": True,
    "docker_url": "unix:///var/run/docker.sock",
}

with DAG(
    dag_id="transformations",
    description="Run dbt models and tests on customer transactions",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,  # triggered by ingestion DAG
    catchup=False,
    default_args=default_args,
    tags=["platform", "transformations"],
) as dag:

    dbt_run = DockerOperator(
        task_id="dbt_run",
        command="dbt run --profiles-dir /dbt --project-dir /dbt",
        **DOCKER_KWARGS,
    )

    dbt_test = DockerOperator(
        task_id="dbt_test",
        command="dbt test --profiles-dir /dbt --project-dir /dbt",
        **DOCKER_KWARGS,
    )

    dbt_run >> dbt_test