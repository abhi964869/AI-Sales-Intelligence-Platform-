import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
import os
from dotenv import load_dotenv
import google.generativeai as genai
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="AI Sales Intelligence Platform",
    page_icon="📊",
    layout="wide"
)
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.0-flash")
st.divider()

def generate_pdf_report(ai_text, total_sales, total_profit, total_orders):
    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    story = []

    story.append(Paragraph("<b>AI Sales Intelligence Report</b>", styles["Title"]))

    story.append(Paragraph(f"Total Sales: ${total_sales:,.2f}", styles["BodyText"]))
    story.append(Paragraph(f"Total Profit: ${total_profit:,.2f}", styles["BodyText"]))
    story.append(Paragraph(f"Total Orders: {total_orders}", styles["BodyText"]))

    story.append(Paragraph("<br/><b>AI Analysis</b>", styles["Heading2"]))
    story.append(Paragraph(ai_text.replace("\n", "<br/>"), styles["BodyText"]))

    doc.build(story)

    buffer.seek(0)

    return buffer

st.subheader("💬 Ask AI About Your Sales")

user_question = st.text_input(
    "Ask any question about your sales data"
)

st.markdown(
    """
    <style>
    .main{
        background-color:#f8fafc;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 AI Sales Intelligence Platform")
st.caption("Interactive Sales Analytics Dashboard")
st.sidebar.title("📂 Data Source")

data_source = st.sidebar.radio(
    "Choose Data Source",
    (
        "MySQL Database",
        "Upload CSV",
        "Upload Excel"
    )
)
uploaded_file = None

if data_source == "Upload CSV":
    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV File",
        type=["csv"]
    )

elif data_source == "Upload Excel":
    uploaded_file = st.sidebar.file_uploader(
        "Upload Excel File",
        type=["xlsx", "xls"]
    )


# ---------------- DATABASE ---------------- #

@st.cache_resource
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sarita@98388",
        database="ai_sales"
    )

conn = get_connection()

if not conn.is_connected():
    conn.reconnect()

query = """
SELECT
row_id,
order_id,
order_date,
ship_date,
ship_mode,
customer_name,
segment,
country_region,
city,
state_province,
region,
category,
sub_category,
product_name,
sales,
quantity,
discount,
profit
FROM superstore
"""
# ---------- LOAD DATA ----------

if data_source == "MySQL Database":
    df = pd.read_sql(query, conn)

else:
    if uploaded_file is None:
        st.info("Please upload a CSV or Excel file.")
        st.stop()

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    st.info(f"📂 File: {uploaded_file.name}")
    st.success(f"✅ Loaded {len(df):,} rows and {len(df.columns)} columns")

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("/", "_")
)
required_columns = [
    "sales",
    "profit",
    "quantity",
    "category",
    "sub_category",
    "region",
    "order_date"
]

missing = [c for c in required_columns if c not in df.columns]

if missing:
    st.error(f"Missing columns: {missing}")
    st.stop()
# ---------- AUTO COLUMN MAPPING ----------

# ---------- AUTO COLUMN MAPPING ----------

column_aliases = {
    "sales": [
        "sales", "sale", "sales_amount", "amount",
        "revenue", "revenue_amount", "turnover"
    ],

    "profit": [
        "profit", "net_profit", "income",
        "earnings", "net_income"
    ],

    "customer_name": [
        "customer", "customer_name",
        "client", "client_name", "buyer"
    ],

    "product_name": [
        "product", "product_name",
        "item", "item_name"
    ],

    "category": [
        "category", "product_category"
    ],

    "sub_category": [
        "sub_category", "subcategory",
        "sub-category"
    ],

    "region": [
        "region", "state", "location",
        "area", "zone"
    ],

    "quantity": [
        "quantity", "qty", "units"
    ],

    "discount": [
        "discount", "discount_percent"
    ],

    "order_date": [
        "order_date", "date",
        "orderdate", "invoice_date"
    ]
}

rename_dict = {}

for standard_name, aliases in column_aliases.items():

    for col in df.columns:

        if col.lower() in aliases:
            rename_dict[col] = standard_name
            break

df.rename(columns=rename_dict, inplace=True)

required_columns = [
    "order_date",
    "customer_name",
    "region",
    "category",
    "sub_category",
    "product_name",
    "sales",
    "quantity",
    "discount",
    "profit"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:

    st.warning(
        "Some columns couldn't be identified automatically."
    )

    st.subheader("🔧 Map Remaining Columns")

    for col in missing_columns:

        selected = st.selectbox(
            f"Select column for '{col}'",
            ["-- Select --"] + list(df.columns),
            key=col
        )

        if selected != "-- Select --":
            df.rename(columns={selected: col}, inplace=True)

    missing_columns = [
        c for c in required_columns
        if c not in df.columns
    ]

    if missing_columns:
        st.error(
            "Still missing: " + ", ".join(missing_columns)
        )
        st.stop()

    st.success("✅ Dataset mapped successfully!")

df["order_date"] = pd.to_datetime(df["order_date"])
if "ship_date" in df.columns:
    df["ship_date"] = pd.to_datetime(df["ship_date"])

df["Year"] = df["order_date"].dt.year
df["Month"] = df["order_date"].dt.strftime("%b")

# ---------------- SIDEBAR ---------------- #
st.sidebar.title("Dashboard Filters")

category = st.sidebar.multiselect(
    "Category",
    sorted(df["category"].unique()),
    default=sorted(df["category"].unique())
)

region = st.sidebar.multiselect(
    "Region",
    sorted(df["region"].unique()),
    default=sorted(df["region"].unique())
)

segment = []
if "segment" in df.columns:
    segment = st.sidebar.multiselect(
        "Segment",
        sorted(df["segment"].unique()),
        default=sorted(df["segment"].unique())
    )
else:
    segment = df.get("segment", pd.Series()).unique().tolist() if "segment" in df.columns else []

year = st.sidebar.multiselect(
    "Year",
    sorted(df["Year"].unique()),
    default=sorted(df["Year"].unique())
)

filtered_df = df[
    (df["category"].isin(category)) &
    (df["region"].isin(region)) &
    (df["Year"].isin(year))
]

if "segment" in df.columns and segment:
    filtered_df = filtered_df[filtered_df["segment"].isin(segment)]

# ---------------- KPI ---------------- #

total_sales = filtered_df["sales"].sum()
total_profit = filtered_df["profit"].sum()
total_orders = filtered_df["order_id"].nunique()
total_quantity = filtered_df["quantity"].sum()

c1,c2,c3,c4 = st.columns(4)

c1.metric("💰 Total Sales",f"${total_sales:,.2f}")
c2.metric("📈 Total Profit",f"${total_profit:,.2f}")
c3.metric("📦 Orders",total_orders)
c4.metric("🛒 Quantity",total_quantity)

st.divider()# ---------------- SALES BY CATEGORY ---------------- #

st.subheader("📊 Sales by Category")

sales_category = (
    filtered_df.groupby("category", as_index=False)["sales"]
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

st.plotly_chart(fig1, use_container_width=True)

# ---------------- SALES BY REGION ---------------- #

st.subheader("🌍 Sales by Region")

sales_region = (
    filtered_df.groupby("region", as_index=False)["sales"]
    .sum()
    .sort_values("sales", ascending=False)
)

fig2 = px.pie(
    sales_region,
    names="region",
    values="sales",
    hole=0.45,
    title="Sales Distribution by Region"
)

st.plotly_chart(fig2, use_container_width=True)

# ---------------- MONTHLY SALES ---------------- #

st.subheader("📈 Monthly Sales Trend")

monthly_sales = (
    filtered_df.groupby(["Year", "Month"], as_index=False)["sales"]
    .sum()
)

month_order = [
    "Jan","Feb","Mar","Apr","May","Jun",
    "Jul","Aug","Sep","Oct","Nov","Dec"
]

monthly_sales["Month"] = pd.Categorical(
    monthly_sales["Month"],
    categories=month_order,
    ordered=True
)

monthly_sales = monthly_sales.sort_values(
    ["Year", "Month"]
)

fig3 = px.line(
    monthly_sales,
    x="Month",
    y="sales",
    color="Year",
    markers=True,
    title="Monthly Sales"
)

st.plotly_chart(fig3, use_container_width=True)

# ---------------- PROFIT BY CATEGORY ---------------- #

st.subheader("💰 Profit by Category")

profit_category = (
    filtered_df.groupby("category", as_index=False)["profit"]
    .sum()
)

fig4 = px.bar(
    profit_category,
    x="category",
    y="profit",
    color="category",
    text_auto=".2s",
    title="Profit by Category"
)

st.plotly_chart(fig4, use_container_width=True)

# ---------------- TOP PRODUCTS ---------------- #

st.subheader("🏆 Top 10 Products")

top_products = (
    filtered_df.groupby("product_name", as_index=False)["sales"]
    .sum()
    .sort_values("sales", ascending=False)
    .head(10)
)

st.dataframe(
    top_products,
    use_container_width=True,
    hide_index=True
)

# ---------------- TOP CUSTOMERS ---------------- #

st.subheader("👥 Top 10 Customers")

top_customers = (
    filtered_df.groupby("customer_name", as_index=False)["sales"]
    .sum()
    .sort_values("sales", ascending=False)
    .head(10)
)

st.dataframe(
    top_customers,
    use_container_width=True,
    hide_index=True
)

st.divider()# ---------------- SEARCH ---------------- #

st.sidebar.divider()
st.sidebar.subheader("🔍 Search")

search = st.sidebar.text_input(
    "Search Product"
)

if search:
    filtered_df = filtered_df[
        filtered_df["product_name"]
        .str.contains(search, case=False, na=False)
    ]

# ---------------- DISCOUNT ANALYSIS ---------------- #

st.subheader("🎯 Discount vs Profit")

discount_profit = (
    filtered_df.groupby("discount", as_index=False)["profit"]
    .sum()
)

fig5 = px.scatter(
    filtered_df,
    x="discount",
    y="profit",
    color="category",
    hover_name="product_name",
    size="sales",
    title="Discount vs Profit"
)

st.plotly_chart(fig5, use_container_width=True)

# ---------------- QUANTITY BY CATEGORY ---------------- #

st.subheader("📦 Quantity Sold by Category")

qty = (
    filtered_df.groupby("category", as_index=False)["quantity"]
    .sum()
)

fig6 = px.bar(
    qty,
    x="category",
    y="quantity",
    color="category",
    title="Quantity Sold"
)

st.plotly_chart(fig6, use_container_width=True)

# ---------------- FULL DATA ---------------- #

st.subheader("📄 Sales Records")

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)
st.download_button(
    "📥 Download Processed Data",
    filtered_df.to_csv(index=False),
    file_name="processed_sales.csv",
    mime="text/csv"
)

# ---------------- DOWNLOAD CSV ---------------- #

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇ Download CSV",
    data=csv,
    file_name="filtered_sales.csv",
    mime="text/csv"
)

# ---------------- QUICK BUSINESS INSIGHTS ---------------- #

st.subheader("📈 Business Insights")

best_category = (
    filtered_df.groupby("category")["sales"]
    .sum()
    .idxmax()
)

best_region = (
    filtered_df.groupby("region")["sales"]
    .sum()
    .idxmax()
)

highest_profit = (
    filtered_df.groupby("category")["profit"]
    .sum()
    .idxmax()
)

st.success(f"🏆 Best Selling Category: {best_category}")
st.info(f"🌍 Best Performing Region: {best_region}")
st.success(f"💰 Highest Profit Category: {highest_profit}")

st.divider()

# ---------------- FOOTER ---------------- #

st.markdown("---")

st.caption(
    "AI Sales Intelligence Platform | Built with Python • Streamlit • MySQL • Plotly"
)

# ============================
# AI SALES INSIGHTS
# ============================

st.header("🤖 AI Business Insights")

total_profit = filtered_df["profit"].sum()
total_sales = filtered_df["sales"].sum()

profit_margin = 0

if total_sales > 0:
    profit_margin = (total_profit / total_sales) * 100

best_product = (
    filtered_df.groupby("product_name")["sales"]
    .sum()
    .idxmax()
)

worst_product = (
    filtered_df.groupby("product_name")["sales"]
    .sum()
    .idxmin()
)

best_customer = (
    filtered_df.groupby("customer_name")["sales"]
    .sum()
    .idxmax()
)

best_region = (
    filtered_df.groupby("region")["sales"]
    .sum()
    .idxmax()
)

st.success(f"🏆 Best Selling Product : {best_product}")

st.success(f"👑 Best Customer : {best_customer}")

st.info(f"🌍 Best Region : {best_region}")

st.warning(f"📉 Lowest Selling Product : {worst_product}")

st.metric(
    "Profit Margin",
    f"{profit_margin:.2f}%"
)

st.divider()

# ============================
# DATA EXPORT
# ============================

st.header("📤 Export")

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇ Download Filtered Dataset",
    csv,
    "filtered_sales.csv",
    "text/csv"
)

st.divider()

# ============================
# ABOUT PROJECT
# ============================

with st.expander("📌 About Project"):

    st.markdown("""
### AI Sales Intelligence Platform

#### Features

- Interactive Dashboard
- KPI Cards
- Sidebar Filters
- Sales Trend
- Region Analysis
- Category Analysis
- Product Analysis
- Customer Analysis
- Profit Analysis
- CSV Export

#### Technologies

- Python
- Streamlit
- Plotly
- MySQL
- Pandas

Developer:
Abhishek Yadav
""")

st.divider()

# ============================
# FOOTER
# ============================

st.markdown(
"""
---
<center>

### 🚀 AI Sales Intelligence Platform

Built using Python • Streamlit • MySQL • Plotly

</center>
""",
unsafe_allow_html=True
)
st.divider()

st.subheader("🤖 AI Sales Insights")

if st.button("Generate AI Insights"):

    summary = f"""
    Total Sales: {df['sales'].sum():,.2f}
    Total Profit: {df['profit'].sum():,.2f}
    Total Orders: {len(df)}
    Total Quantity Sold: {df['quantity'].sum()}

    Top Category:
    {df.groupby('category')['sales'].sum().sort_values(ascending=False).head(3).to_string()}

    Top Region:
    {df.groupby('region')['sales'].sum().sort_values(ascending=False).head(4).to_string()}

    Top Customers:
    {df.groupby('customer_name')['sales'].sum().sort_values(ascending=False).head(5).to_string()}
    """

    prompt = f"""
    You are an expert Sales Analyst.

    Analyze this sales data and provide:

    1. Executive Summary
    2. Best Performing Category
    3. Best Region
    4. Top Customer Insights
    5. Business Recommendations
    6. Risks
    7. Growth Opportunities

    Data:

    {summary}
    """

    with st.spinner("Generating AI insights..."):
        response = model.generate_content(prompt)

    st.success("Analysis Complete!")

    st.markdown(response.text)
if user_question:

    context = filtered_df.head(500).to_csv(index=False)

    prompt = f"""
You are a senior business analyst.

Analyze this sales dataset.

Give:
1. Executive Summary
2. Sales Trends
3. Profit Analysis
4. Regional Performance
5. Best Products
6. Worst Products
7. Customer Insights
8. Business Recommendations
9. Risks
10. Action Plan

Dataset:
{context}

Question:
{user_question}
"""

    with st.spinner("Thinking..."):
        answer = model.generate_content(prompt)

    st.markdown("### 🤖 AI Answer")
    st.write(answer.text)

    st.download_button(
        "📄 Download AI Report",
        answer.text,
        file_name="AI_Sales_Report.txt",
        mime="text/plain"
    )
conn.close()