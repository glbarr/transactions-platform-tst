"""
airflow/dags/transformations.py

Runs dbt models individually for granular observability and rerunnability.
Triggered by the ingestion DAG on success.

Task order:
    stg_transactions -> dim_product -> fact_transactions -> fact_monthly_summary -> dbt_test
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
        source=os.environ.get("DBT_PROJECT_DIR"),
        target="/dbt",
        type="bind",
    )
]

DOCKER_KWARGS = {
    "image": DBT_IMAGE,
    "environment": DBT_ENVIRONMENT,
    "mounts": DBT_MOUNTS,
    "network_mode": os.environ.get("DOCKER_NETWORK", "transactions-platform-tst-1_platform_net"),
    "mount_tmp_dir": False,
    "auto_remove": True,
    "docker_url": "unix:///var/run/docker.sock",
}


def dbt_task(task_id: str, model: str) -> DockerOperator:
    return DockerOperator(
        task_id=task_id,
        command=f"dbt run --profiles-dir /dbt --project-dir /dbt --select {model}",
        **DOCKER_KWARGS,
    )


with DAG(
    dag_id="transformations",
    description="Run dbt models on customer transactions",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    default_args=default_args,
    tags=["platform", "transformations"],
) as dag:

    stg_transactions     = dbt_task("stg_transactions",     "stg_transactions")
    dim_product          = dbt_task("dim_product",          "dim_product")
    fact_transactions    = dbt_task("fact_transactions",    "fact_transactions")
    fact_monthly_summary = dbt_task("fact_monthly_summary", "fact_monthly_summary")

    dbt_test = DockerOperator(
        task_id="dbt_test",
        command="dbt test --profiles-dir /dbt --project-dir /dbt",
        **DOCKER_KWARGS,
    )

    dbt_deps = DockerOperator(
    task_id="dbt_deps",
    command="dbt deps --profiles-dir /dbt --project-dir /dbt",
    **DOCKER_KWARGS,
)

dbt_deps >> stg_transactions >> dim_product >> fact_transactions >> fact_monthly_summary >> dbt_test
