import mysql.connector
import pandas as pd

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sarita@98388",
    database="ai_sales"
)

queries = {
    "Top 10 Products by Sales": """
        SELECT product_name,
               ROUND(SUM(sales),2) AS total_sales
        FROM superstore
        GROUP BY product_name
        ORDER BY total_sales DESC
        LIMIT 10;
    """,

    "Top 10 Cities by Sales": """
        SELECT city,
               ROUND(SUM(sales),2) AS total_sales
        FROM superstore
        GROUP BY city
        ORDER BY total_sales DESC
        LIMIT 10;
    """,

    "Top 10 Customers": """
        SELECT customer_name,
               ROUND(SUM(sales),2) AS total_sales
        FROM superstore
        GROUP BY customer_name
        ORDER BY total_sales DESC
        LIMIT 10;
    """,

    "Profit by Category": """
        SELECT category,
               ROUND(SUM(profit),2) AS total_profit
        FROM superstore
        GROUP BY category
        ORDER BY total_profit DESC;
    """
}

for title, query in queries.items():
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)
    df = pd.read_sql(query, conn)
    print(df)

conn.close()