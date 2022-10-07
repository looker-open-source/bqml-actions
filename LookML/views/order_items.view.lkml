view: order_items {
  sql_table_name: `bigquery-public-data.thelook_ecommerce.order_items` ;;
  drill_fields: [order_id, inventory_item_id, sale_price, created_time, returned_time]

  dimension: id {
    primary_key: yes
    type: number
    sql: ${TABLE}.ID ;;
  }

  dimension_group: created {
    type: time
    timeframes: [raw, time, date, week, month, quarter, year]
    sql: ${TABLE}.CREATED_AT ;;
  }

  dimension_group: delivered {
    type: time
    timeframes: [raw, time, date, week, month, quarter, year]
    sql: ${TABLE}.DELIVERED_AT ;;
  }

  dimension: inventory_item_id {
    type: number
    sql: ${TABLE}.INVENTORY_ITEM_ID ;;
  }

  dimension: order_id {
    type: number
    sql: ${TABLE}.ORDER_ID ;;
  }

  dimension_group: returned {
    type: time
    timeframes: [raw, time, date, week, month, quarter, year]
    sql: ${TABLE}.RETURNED_AT ;;
  }

  dimension: sale_price {
    hidden: yes
    type: number
    sql: ${TABLE}.SALE_PRICE ;;
  }

  dimension_group: shipped {
    type: time
    timeframes: [raw, time, date, week, month, quarter, year]
    sql: ${TABLE}.SHIPPED_AT ;;
  }

  dimension: status {
    type: string
    sql: ${TABLE}.STATUS ;;
  }

  dimension: user_id {
    type: number
    sql: ${TABLE}.USER_ID ;;
  }
  
  measure: last_order_date {
    view_label: "Customers"
    type: date
    sql: MAX(${created_date}) ;;
  }

  measure: number_of_orders {
    view_label: "Customers"
    type: count_distinct
    sql: ${order_id} ;;
  }

  measure: average_basket_size {
    view_label: "Customers"
    type: number
    sql: ${inventory_items.number_of_inventory_items} / ${number_of_orders} ;;
    value_format_name: decimal_1
  }

  measure: average_basket_value{
    view_label: "Customers"
    type: sum
    sql: ${sale_price} ;;
    value_format_name: usd
  }

  measure: return_count {
    view_label: "Customers"
    type: count_distinct
    sql: ${returned_raw} ;;
  }

  measure: has_returns {
    view_label: "Customers"
    type: string # setting as string as BQML will auto cast bool to a string. This causes issues in ML.PREDICT functions
    sql: CAST(${return_count} > 0 AS string) ;;
  }

  measure: total_returns {
    view_label: "Customers"
    type: sum
    sql: ${sale_price} ;;
    filters: [returned_time: "NOT NULL"]
    value_format_name: usd
  }

  measure: gross_sales {
    view_label: "Customers"
    type: sum
    sql: ${sale_price} ;;
    value_format_name: usd
  }

  measure: net_sales {
    view_label: "Customers"
    type: number
    sql: ${gross_sales} - ${total_returns} ;;
    value_format_name: usd
  }

  measure: average_sales_per_customer {
    type: number
    sql: ${gross_sales} / ${customers.number_of_customers} ;;
    value_format_name: usd
  }

}
