import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

st.set_page_config(
    page_title="AI Sales Dashboard",
    layout="wide"
)

st.title("📊 AI Sales Intelligence Dashboard")

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sarita@98388",
    database="ai_sales"
)

# SQL Query
query = """
SELECT
    product_name AS category,
    SUM(quantity * price) AS total_sales
FROM sales
GROUP BY product_name
"""

# Read data
df = pd.read_sql(query, conn)

# KPI
st.metric("Total Sales", f"₹{df['total_sales'].sum():,.2f}")

st.divider()

# Chart
fig = px.bar(
    df,
    x="category",
    y="total_sales",
    color="category",
    title="Sales by Product"
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Sales Summary")

st.dataframe(df, use_container_width=True)

conn.close()