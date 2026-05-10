-- models/staging/stg_transactions.sql
--
-- Cleans and casts raw.customer_transactions.
--
-- Design decisions:
-- - Non-numeric price/tax values (e.g. "Two Hundred", "Fifteen") are cast to NULL
--   and flagged with _dq_issue = true. Rows are not dropped — quarantine approach.
-- - customer_id and quantity stored as floats in source (e.g. 501.0) — cast to integer
--   after null handling.
-- - transaction_id=T1090 has a non-integer prefix — flagged as DQ issue.
-- - total_amount = (price * quantity) + tax — tax is an absolute amount, not a rate.
-- - Rows with _dq_issue = true are excluded from fact models downstream.

with source as (
    select * from raw.customer_transactions
),

cleaned as (
    select
        -- transaction_id: strip non-numeric prefix if present, cast to integer
        case
            when transaction_id ~ '^\d+$' then transaction_id::integer
            else null
        end                                                         as transaction_id,

        -- customer_id: stored as float in source (501.0), cast to integer
        case
            when customer_id is null or customer_id = '' then null
            else customer_id::float::integer
        end                                                         as customer_id,

        -- transaction_date: cast to date
        case
            when transaction_date is null or transaction_date = '' then null
            else transaction_date::date
        end                                                         as transaction_date,

        product_id::integer                                         as product_id,
        trim(product_name)                                          as product_name,

        -- quantity: stored as float in source (1.0), cast to integer
        case
            when quantity is null or quantity = '' then null
            else quantity::float::integer
        end                                                         as quantity,

        -- price: cast to numeric, non-numeric strings become null
        case
            when price ~ '^\d+(\.\d+)?$' then price::numeric(10, 2)
            else null
        end                                                         as price,

        -- tax: cast to numeric, non-numeric strings become null
        case
            when tax ~ '^\d+(\.\d+)?$' then tax::numeric(10, 2)
            else null
        end                                                         as tax,

        -- data quality flag
        case
            when transaction_id !~ '^\d+$'         then true
            when price !~ '^\d+(\.\d+)?$'           then true
            when tax !~ '^\d+(\.\d+)?$'             then true
            when customer_id is null or customer_id = '' then true
            when quantity is null or quantity = ''   then true
            else false
        end                                                         as _dq_issue,

        _ingested_at

    from source
),

final as (
    select
        *,
        -- total_amount only for clean rows
        case
            when not _dq_issue
            then (price * quantity) + tax
            else null
        end                                                         as total_amount
    from cleaned
)

select * from final