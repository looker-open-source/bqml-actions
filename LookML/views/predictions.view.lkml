view: predictions {
  derived_table: {
    sql: SELECT * FROM ML.PREDICT(
          MODEL `bqml.model_{% parameter model_name %}`,
          (SELECT * FROM `bqml.view_{% parameter model_name %}`));;
  }

  parameter: model_name {
    type: unquoted
    suggest_explore: bqml_models
    suggest_dimension: model_name
  }

  dimension: customers_id {
    hidden: yes
    primary_key: yes
    sql: ${TABLE}.customers_id ;;
  }

  # The output column for BigQuery ML.PREDICT function will be predicted_<label_column_name>
  # https://cloud.google.com/bigquery-ml/docs/reference/standard-sql/bigqueryml-syntax-predict
  measure: predicted_net_sales {
    type: max
    sql: ${TABLE}.predicted_order_items_net_sales ;;
    value_format_name: usd
  }

  measure: residual {
    description: "Difference between the observed value of total sales and the predicted total sales"
    type:  number
    sql: ${predicted_net_sales} - ${order_items.net_sales}  ;;
    value_format_name: usd
  }

  measure: residual_percent {
    type:  number
    sql: ABS(1.0 * ${residual} / NULLIF(${predicted_net_sales}, 0))  ;;
    value_format_name: percent_1
  }

}
