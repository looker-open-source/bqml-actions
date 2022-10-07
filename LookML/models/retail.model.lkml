connection: "INPUT_YOUR_BQ_CONNECTION_HERE" # <- Replace with your connection name

include: "/views/*.view"

explore: order_items {
  label: "Orders 🏷"
  always_filter: {
    filters: [predictions.model_name: ""]
  }

  join: customers {
    type:  left_outer
    relationship: many_to_one
    sql_on: ${order_items.user_id} = ${customers.id} ;;
  }

  join: inventory_items {
    type:  left_outer
    relationship: many_to_one
    view_label: "Products"
    sql_on: ${order_items.inventory_item_id} = ${inventory_items.id} ;;
  }

  join: products {
    relationship: many_to_one
    sql_on: ${inventory_items.product_id} = ${products.id} ;;
  }

  join: predictions {
    relationship: one_to_one
    sql_on: ${predictions.customers_id} = ${customers.id} ;;
  }
}

explore: bqml_models {}
