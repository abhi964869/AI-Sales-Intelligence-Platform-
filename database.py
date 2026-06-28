import pandas as pd
import mysql.connector
import glob

# Find Excel file automatically
excel_file = glob.glob("data/*.xls")[0]

# Read Excel
df = pd.read_excel(excel_file, sheet_name="Orders")

# Convert dates
df["Order Date"] = pd.to_datetime(df["Order Date"])
df["Ship Date"] = pd.to_datetime(df["Ship Date"])

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sarita@98388",
    database="ai_sales"
)

cursor = conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS superstore (
    row_id INT,
    order_id VARCHAR(50),
    order_date DATE,
    ship_date DATE,
    ship_mode VARCHAR(50),
    customer_id VARCHAR(50),
    customer_name VARCHAR(100),
    segment VARCHAR(50),
    country_region VARCHAR(100),
    city VARCHAR(100),
    state_province VARCHAR(100),
    postal_code VARCHAR(20),
    region VARCHAR(50),
    product_id VARCHAR(50),
    category VARCHAR(50),
    sub_category VARCHAR(50),
    product_name VARCHAR(255),
    sales DECIMAL(10,2),
    quantity INT,
    discount DECIMAL(5,2),
    profit DECIMAL(10,2)
)
""")

# Remove old data if any
cursor.execute("DELETE FROM superstore")

# Insert data
for _, row in df.iterrows():
    cursor.execute("""
    INSERT INTO superstore(
        row_id,
        order_id,
        order_date,
        ship_date,
        ship_mode,
        customer_id,
        customer_name,
        segment,
        country_region,
        city,
        state_province,
        postal_code,
        region,
        product_id,
        category,
        sub_category,
        product_name,
        sales,
        quantity,
        discount,
        profit
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        int(row["Row ID"]),
        row["Order ID"],
        row["Order Date"].date(),
        row["Ship Date"].date(),
        row["Ship Mode"],
        row["Customer ID"],
        row["Customer Name"],
        row["Segment"],
        row["Country/Region"],
        row["City"],
        row["State/Province"],
        str(row["Postal Code"]),
        row["Region"],
        row["Product ID"],
        row["Category"],
        row["Sub-Category"],
        row["Product Name"],
        float(row["Sales"]),
        int(row["Quantity"]),
        float(row["Discount"]),
        float(row["Profit"])
    ))

conn.commit()

print(f"Successfully imported {len(df)} rows into MySQL!")

cursor.close()
conn.close()