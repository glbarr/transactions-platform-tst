FROM transactions/airflow:2.9.1

USER airflow
RUN pip install --no-cache-dir \
    dbt-core==1.9.0 \
    dbt-postgres==1.9.0

WORKDIR /dbt

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["dbt"]