import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import os
from dotenv import load_dotenv

# ==========================
# PAGE CONFIG
# ==========================

st.set_page_config(
    page_title="AI Sales Intelligence Platform",
    page_icon="📊",
    layout="wide"
)

st.title("📊 AI Sales Intelligence Platform")
st.caption("Upload your Sales Dataset and get AI-powered insights.")

# ==========================
# LOAD GEMINI API
# ==========================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY not found.")
    st.stop()

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash")

# ==========================
# FILE UPLOAD
# ==========================

st.sidebar.header("📂 Upload Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Choose CSV or Excel file",
    type=["csv", "xlsx"]
)

if uploaded_file is None:
    st.info("👈 Upload a CSV or Excel file to continue.")
    st.stop()

# ==========================
# READ FILE
# ==========================

try:

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)

    else:
        df = pd.read_excel(uploaded_file)

except Exception as e:

    st.error(f"Unable to read file.\n\n{e}")
    st.stop()

# ==========================
# CLEAN COLUMN NAMES
# ==========================

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("-", "_")
)

# ==========================
# SHOW FILE DETAILS
# ==========================

st.success("✅ File Loaded Successfully")

col1, col2, col3 = st.columns(3)

col1.metric("Rows", len(df))
col2.metric("Columns", len(df.columns))
col3.metric("File", uploaded_file.name)

st.subheader("Preview")

st.dataframe(df.head(), use_container_width=True)

st.divider()
# ==========================
# AUTO COLUMN MAPPING
# ==========================

column_aliases = {

    "sales": [
        "sales","sale","amount","revenue",
        "sales_amount","total_sales"
    ],

    "profit": [
        "profit","net_profit","earnings",
        "income","net_income"
    ],

    "quantity": [
        "quantity","qty","units"
    ],

    "category": [
        "category","product_category"
    ],

    "sub_category": [
        "sub_category","subcategory",
        "sub-category"
    ],

    "product_name": [
        "product","product_name",
        "item","item_name"
    ],

    "customer_name": [
        "customer","customer_name",
        "client","buyer"
    ],

    "region": [
        "region","state",
        "location","zone"
    ],

    "order_date": [
        "order_date","date",
        "invoice_date"
    ]
}

rename_dict = {}

for standard_name, aliases in column_aliases.items():

    for column in df.columns:

        if column.lower() in aliases:

            rename_dict[column] = standard_name
            break

df.rename(columns=rename_dict, inplace=True)

# ==========================
# MANUAL COLUMN MAPPING
# ==========================

required_columns = [
    "sales",
    "profit",
    "quantity",
    "category",
    "product_name",
    "customer_name",
    "region"
]

missing = [
    col for col in required_columns
    if col not in df.columns
]

if missing:

    st.warning("Some columns could not be detected automatically.")

    st.subheader("🔧 Map Remaining Columns")

    for col in missing:

        selected = st.selectbox(
            f"Select column for '{col}'",
            df.columns,
            key=col
        )

        df.rename(
            columns={selected: col},
            inplace=True
        )

# ==========================
# KPI SECTION
# ==========================

st.divider()

st.header("📈 Dashboard Overview")

total_sales = df["sales"].sum()

total_profit = df["profit"].sum()

total_quantity = df["quantity"].sum()

total_orders = len(df)

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "💰 Total Sales",
    f"${total_sales:,.2f}"
)

k2.metric(
    "📈 Total Profit",
    f"${total_profit:,.2f}"
)

k3.metric(
    "📦 Total Orders",
    total_orders
)

k4.metric(
    "🛒 Quantity Sold",
    f"{total_quantity:,}"
)

st.divider()
# ==========================
# SIDEBAR FILTERS
# ==========================

st.sidebar.header("🎛 Dashboard Filters")

category_filter = st.sidebar.multiselect(
    "Category",
    sorted(df["category"].dropna().unique()),
    default=sorted(df["category"].dropna().unique())
)

region_filter = st.sidebar.multiselect(
    "Region",
    sorted(df["region"].dropna().unique()),
    default=sorted(df["region"].dropna().unique())
)

filtered_df = df[
    (df["category"].isin(category_filter)) &
    (df["region"].isin(region_filter))
]

st.sidebar.success(
    f"Showing {len(filtered_df):,} records"
)

# ==========================
# SALES BY CATEGORY
# ==========================

st.header("📊 Sales Analysis")

sales_category = (
    filtered_df
    .groupby("category", as_index=False)["sales"]
    .sum()
    .sort_values("sales", ascending=False)
)

fig1 = px.bar(
    sales_category,
    x="category",
    y="sales",
    color="category",
    text_auto=".2s",
    title="Sales by Category"
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

# ==========================
# SALES BY REGION
# ==========================

sales_region = (
    filtered_df
    .groupby("region", as_index=False)["sales"]
    .sum()
)

fig2 = px.pie(
    sales_region,
    names="region",
    values="sales",
    hole=0.45,
    title="Sales Distribution by Region"
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

# ==========================
# MONTHLY SALES TREND
# ==========================

if "order_date" in filtered_df.columns:

    filtered_df["order_date"] = pd.to_datetime(
        filtered_df["order_date"],
        errors="coerce"
    )

    filtered_df["Month"] = (
        filtered_df["order_date"]
        .dt.to_period("M")
        .astype(str)
    )

    monthly_sales = (
        filtered_df
        .groupby("Month", as_index=False)["sales"]
        .sum()
    )

    fig3 = px.line(
        monthly_sales,
        x="Month",
        y="sales",
        markers=True,
        title="Monthly Sales Trend"
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

# ==========================
# TOP PRODUCTS
# ==========================

st.subheader("🏆 Top 10 Products")

top_products = (
    filtered_df
    .groupby("product_name", as_index=False)["sales"]
    .sum()
    .sort_values("sales", ascending=False)
    .head(10)
)

st.dataframe(
    top_products,
    use_container_width=True,
    hide_index=True
)

# ==========================
# TOP CUSTOMERS
# ==========================

st.subheader("👥 Top 10 Customers")

top_customers = (
    filtered_df
    .groupby("customer_name", as_index=False)["sales"]
    .sum()
    .sort_values("sales", ascending=False)
    .head(10)
)

st.dataframe(
    top_customers,
    use_container_width=True,
    hide_index=True
)

st.divider()
# ==========================
# AI INSIGHTS
# ==========================

st.header("🤖 AI Business Insights")

summary = f"""
Dataset Shape: {df.shape}

Total Sales: {df['sales'].sum():,.2f}

Total Profit: {df['profit'].sum():,.2f}

Total Quantity: {df['quantity'].sum():,.0f}

Top Categories

{df.groupby('category')['sales'].sum().sort_values(ascending=False).head(5).to_string()}

Top Regions

{df.groupby('region')['sales'].sum().sort_values(ascending=False).head(5).to_string()}

Top Products

{df.groupby('product_name')['sales'].sum().sort_values(ascending=False).head(10).to_string()}
"""

if st.button("🚀 Generate AI Insights"):

    prompt = f"""
You are a Senior Business Analyst.

Analyze this sales dataset.

Provide:

1. Executive Summary
2. Sales Trends
3. Profit Analysis
4. Best Categories
5. Best Regions
6. Growth Opportunities
7. Risks
8. Business Recommendations

Dataset

{summary}
"""

    with st.spinner("Generating AI Insights..."):

        response = model.generate_content(prompt)

    st.success("Analysis Complete")

    st.markdown(response.text)

# ==========================
# ASK AI
# ==========================

st.divider()

st.header("💬 Ask AI About Your Data")

question = st.text_input(
    "Ask anything about your uploaded dataset"
)

if question:

    prompt = f"""
You are an expert Data Analyst.

Dataset

{summary}

Question

{question}

Answer in simple business language.
"""

    with st.spinner("Thinking..."):

        answer = model.generate_content(prompt)

    st.markdown(answer.text)

st.divider()
# ==========================
# DOWNLOAD DATA
# ==========================

st.header("📥 Download")

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇ Download Filtered CSV",
    csv,
    "filtered_sales.csv",
    "text/csv"
)

# ==========================
# PROJECT INFO
# ==========================

with st.expander("📌 About This Project"):

    st.markdown("""
### AI Sales Intelligence Platform

#### Features

- CSV Upload
- Excel Upload
- Auto Column Mapping
- KPI Dashboard
- Interactive Charts
- AI Insights
- Ask AI
- Download CSV

#### Built With

- Python
- Streamlit
- Pandas
- Plotly
- Gemini AI
""")

# ==========================
# FOOTER
# ==========================

st.markdown("---")

st.caption(
    "Built by Abhishek Yadav | AI Sales Intelligence Platform"
)