-- models/dimensions/dim_product.sql
--
-- Product dimension table.
--
-- Design decisions:
-- - Distinct products derived from staging — no separate product source exists.
-- - Excludes rows with _dq_issue = true to avoid polluting the dimension
--   with corrupt product data.
-- - surrogate_key generated via dbt_utils to give a stable integer-free PK
--   that survives source system changes.

with source as (
    select distinct
        product_id,
        product_name
    from {{ ref('stg_transactions') }}
    where not _dq_issue
      and product_id is not null
      and product_name is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['product_id']) }}  as product_sk,
    product_id,
    product_name
from source
order by product_id