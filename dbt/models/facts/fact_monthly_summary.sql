-- models/facts/fact_monthly_summary.sql
--
-- Monthly aggregated metrics per product.
--
-- Design decisions:
-- - Builds on fact_transactions (already clean, no need to re-filter DQ)
-- - Aggregates by month + product — useful for trend analysis and BI
-- - Includes transaction count, total revenue, total tax, total quantity
-- - materialized as table: small aggregate, cheap to fully rebuild

{{
    config(
        materialized='table',
        schema='transformed'
    )
}}

with base as (
    select
        date_trunc('month', transaction_date)   as month,
        product_id,
        product_name,
        transaction_id,
        quantity,
        price,
        tax,
        total_amount
    from {{ ref('fact_transactions') }}
)

select
    month,
    product_id,
    product_name,
    count(transaction_id)                       as transaction_count,
    sum(quantity)                               as total_quantity,
    round(sum(price * quantity), 2)             as total_revenue_ex_tax,
    round(sum(tax), 2)                          as total_tax,
    round(sum(total_amount), 2)                 as total_revenue_inc_tax
from base
group by month, product_id, product_name
order by month, product_id