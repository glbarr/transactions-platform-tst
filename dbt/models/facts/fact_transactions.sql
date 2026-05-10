-- models/facts/fact_transactions.sql
--
-- One row per valid transaction.
--
-- Design decisions:
-- - Excludes rows with _dq_issue = true — corrupt data must not pollute metrics
-- - Joins to dim_product for the surrogate key — fact table stores SK not NK
-- - Excludes rows where quantity or price are null — cannot compute meaningful measures
-- - incremental model: on reruns only new transaction_ids are merged in

{{
    config(
        materialized='incremental',
        unique_key='transaction_id',
        incremental_strategy='merge'
    )
}}

with staged as (
    select *
    from {{ ref('stg_transactions') }}
    where not _dq_issue
      and quantity is not null
      and price is not null
      and tax is not null
),

joined as (
    select
        s.transaction_id,
        s.customer_id,
        s.transaction_date,
        d.product_sk,
        s.product_id,
        s.product_name,
        s.quantity,
        s.price,
        s.tax,
        s.total_amount,
        s._ingested_at
    from staged s
    left join {{ ref('dim_product') }} d
        on s.product_id = d.product_id
)

select *
from joined

{% if is_incremental() %}
    where transaction_id not in (select transaction_id from {{ this }})
{% endif %}
