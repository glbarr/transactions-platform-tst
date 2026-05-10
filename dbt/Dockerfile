FROM ghcr.io/dbt-labs/dbt-postgres:1.8.0
 
COPY packages.yml /dbt/packages.yml
 
WORKDIR /dbt
 
RUN dbt deps --profiles-dir /dbt