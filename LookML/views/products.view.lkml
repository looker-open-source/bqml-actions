view: products {
  sql_table_name: `bigquery-public-data.thelook_ecommerce.products` ;;
  drill_fields: [id, sku, brand, category, department]

  dimension: id {
    primary_key: yes
    type: number
    hidden: yes
    sql: ${TABLE}.ID ;;
  }

  dimension: brand {
    type: string
    sql: ${TABLE}.BRAND ;;
    drill_fields: [name]
  }

  dimension: category {
    type: string
    sql: ${TABLE}.CATEGORY ;;
    drill_fields: [stores.name,brand]
  }

  dimension: department {
    label: "Target Gender"
    type: string
    sql: ${TABLE}.DEPARTMENT ;;
  }

  dimension: name {
    label: "Product Name"
    type: string
    sql: ${TABLE}.NAME ;;
  }

  dimension: sku {
    type: string
    sql: ${TABLE}.SKU ;;
  }

  dimension: area {
    type: string
    sql: CASE
      WHEN ${category} IN ('Accessories', 'Swim', 'Socks', 'Socks & Hosiery', 'Leggings', 'Plus', 'Sleep & Lounge') THEN 'Accessories'
      WHEN ${category} IN ('Jeans', 'Tops & Tees', 'Shorts', 'Sweaters', 'Underwear', 'Intimates', 'Jumpsuits & Rompers', 'Maternity') THEN 'Casual Wear'
      WHEN ${category} IN ('Dresses', 'Skirts', 'Blazers & Jackets', 'Pants', 'Pants & Capris', 'Suits') THEN 'Formal Wear'
      WHEN ${category} IN ('Clothing Sets', 'Suits & Sport Coats', 'Outerwear & Coats', 'Fashion Hoodies & Sweatshirts', 'Suits', 'Active') THEN 'Outerwear'
    END;;
    drill_fields: [category]
  }

  dimension: product_image {
    type: string
    sql: ${name} ;;
  }

  measure: number_of_products {
    type: count_distinct
    sql: ${id} ;;
  }

  measure: list_of_products {
    type: list
    list_field: name
  }
}
