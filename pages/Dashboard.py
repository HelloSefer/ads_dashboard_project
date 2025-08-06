import streamlit as st
import pandas as pd
import plotly.express as px
import time
import mysql.connector
import os
from dotenv import load_dotenv 

load_dotenv()
def inject_custom_css():
   st.markdown("""
<style>
body {
    background: #0d0d1a;
}
.stApp {
    background: linear-gradient(to bottom right, #001f33, #330000);
    color: #f0f0f0;
    font-family: 'Segoe UI', sans-serif;
    overflow: hidden;
}
h1, h2, h3 {
    color: #ff8c00;
    text-shadow: 0 0 12px #81d4fa, 0 0 15px #ff5722;
}
[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #003366, #4a0f00);
    box-shadow: inset 0 0 25px #ff6f00, 0 0 40px #29b6f6;
    border-radius: 10px;
    color: #ffffff;
    animation: glowSidebar 4s ease-in-out infinite;
}
@keyframes glowSidebar {
    0%, 100% { box-shadow: inset 0 0 25px #ff6f00, 0 0 30px #29b6f6; }
    50% { box-shadow: inset 0 0 35px #29b6f6, 0 0 50px #ff8c00; }
}
[data-testid="stSidebar"] label {
    font-weight: bold;
    color: #ffe082;
}
[data-testid="stSidebar"] ::-webkit-scrollbar { width: 8px; }
[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
    background: #29b6f6;
    border-radius: 4px;
}
label {
    color: #ffe082 !important;
    font-weight: 600;
    font-size: 1.05rem;
    text-shadow: 0 0 4px #29b6f6;
}
input[type="text"], input[type="number"] {
    background-color: #2a2a2a;
    color: #ffffff;
    border: 2px solid #ff6f00;
    border-radius: 10px;
    padding: 0.5rem;
    font-size: 1rem;
    transition: 0.3s;
}
input[type="text"]:focus, input[type="number"]:focus {
    outline: none;
    border-color: #29b6f6;
    box-shadow: 0 0 10px #29b6f6;
}
.stButton button {
    background: linear-gradient(to right, #ff6f00, #29b6f6);
    border: none;
    padding: 0.7rem 1.5rem;
    border-radius: 25px;
    color: white;
    font-weight: bold;
    font-size: 1rem;
    box-shadow: 0 0 15px #ff8c00;
    transition: 0.3s ease;
}
.stButton button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 30px #81d4fa;
    background: linear-gradient(to right, #29b6f6, #ff6f00);
}
[data-testid="stForm"] {
    border: 2px solid rgba(255, 111, 0, 0.5);
    border-radius: 15px;
    padding: 2rem;
    box-shadow: 0 0 20px rgba(129, 212, 250, 0.6);
    background-color: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(3px);
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.kpi-box {
    background: linear-gradient(135deg, #0d0d0d, #1a1a1a);
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 0 8px rgba(0,0,0,0.2);
    transition: all 0.3s ease-in-out;
    margin-bottom: 12px;
    text-align: center;
    color: #f2f2f2;
}
.kpi-box:hover {
    transform: scale(1.05);
    box-shadow: 0 0 20px #00ffcc, 0 0 30px rgba(255,255,255,0.1);
}
.blue-border { border-left: 6px solid #3498db; box-shadow: 0 0 10px #3498db; }
.green-border { border-left: 6px solid #2ecc71; box-shadow: 0 0 10px #2ecc71; }
.red-border { border-left: 6px solid #e74c3c; box-shadow: 0 0 10px #e74c3c; }
.kpi-title { font-size: 14px; color: #aaa; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-value { font-size: 26px; font-weight: bold; color: #ffffff; }
</style>
""", unsafe_allow_html=True)
inject_custom_css()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306))  # default 3306 if not found
    )

if "username" not in st.session_state or "role" not in st.session_state:
    st.warning("⚠ Please login from the Home page.")
    st.stop()

username = st.session_state["username"]
role = st.session_state["role"]

st.title(" Ads Campaign Dashboard")

if st.sidebar.button(" Logout"):
    st.session_state.clear()
    st.switch_page("Home.py")

try:
    conn = get_db_connection()
    df = pd.read_sql("SELECT * FROM campaigns", conn)
    conn.close()

    df.columns = df.columns.str.strip()
    df["date"] = pd.to_datetime(df["date"], errors="coerce", infer_datetime_format=True)
    df["sales"] = df["units_sold"] * df["price_per_unit"]
    if df["date"].isnull().any():
        df = df.dropna(subset=["date"])
except Exception as e:
    st.error(f" Error loading data: {e}")
    st.stop()

if role == "admin":
    try:
        conn = get_db_connection()
        users_df = pd.read_sql("SELECT username, admin FROM users", conn)
        conn.close()

        team_members = users_df[
            (users_df["admin"] == username) | (users_df["username"] == username)
        ]["username"].tolist()

        st.sidebar.subheader(" View by Member")
        selected_user = st.sidebar.selectbox("Choose user", ["ALL"] + team_members)

        if selected_user == "ALL":
            df = df[df["username"].isin(team_members)]
        else:
            df = df[df["username"] == selected_user]
    except Exception as e:
        st.error(f" Error loading users: {e}")
        st.stop()
else:
    df = df[df["username"] == username]

if df.empty:
    st.warning(" No campaigns found for this user.")
    st.stop()

st.sidebar.header(" Filters")
platforms = st.sidebar.multiselect("Platform", df["platform"].unique(), default=df["platform"].unique())
campaigns = st.sidebar.multiselect("Campaign", df["campaign"].unique(), default=df["campaign"].unique())

if df["date"].notna().any():
    min_date, max_date = df["date"].min(), df["date"].max()
else:
    st.warning("⚠ No valid dates available.")
    st.stop()

date_range = st.sidebar.date_input("Date Range", (min_date, max_date))
start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

df_filtered = df[
    (df["platform"].isin(platforms)) &
    (df["campaign"].isin(campaigns)) &
    (df["date"] >= start_date) & (df["date"] <= end_date)
]

if df_filtered.empty:
    st.warning("⚠ No data found for your selection.")
    st.stop()

df_filtered["gross_income"] = df_filtered["sales"]
df_filtered["total_cost"] = (
    (df_filtered["units_sold"] * df_filtered["product_cost"]) +
    df_filtered["delivery_cost"] +
    df_filtered["ad_spend"]
)
df_filtered["net_profit"] = df_filtered["gross_income"] - df_filtered["total_cost"]
df_filtered["roas"] = df_filtered.apply(lambda x: x["sales"] / x["ad_spend"] if x["ad_spend"] > 0 else 0, axis=1)
df_filtered["profit_margin"] = df_filtered.apply(lambda x: (x["net_profit"] / x["gross_income"] * 100) if x["gross_income"] > 0 else 0, axis=1)

total_spend = df_filtered["ad_spend"].sum()
total_sales = df_filtered["sales"].sum()
total_clicks = df_filtered["clicks"].sum()
roas = total_sales / total_spend if total_spend else 0
net_profit = df_filtered["net_profit"].sum()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="kpi-box blue-border"><div class="kpi-title">Ad Spend</div><div class="kpi-value">${total_spend:,.2f}</div></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="kpi-box green-border"><div class="kpi-title">🛒 Sales</div><div class="kpi-value">${total_sales:,.2f}</div></div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="kpi-box red-border"><div class="kpi-title">Clicks</div><div class="kpi-value">{total_clicks:,}</div></div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="kpi-box blue-border"><div class="kpi-title">ROAS</div><div class="kpi-value">{roas:.2f}</div></div>""", unsafe_allow_html=True)

col5, col6 = st.columns(2)
with col5:
    st.markdown(f"""<div class="kpi-box green-border"><div class="kpi-title">Net Profit</div><div class="kpi-value">${net_profit:,.2f}</div></div>""", unsafe_allow_html=True)
with col6:
    st.markdown(f"""<div class="kpi-box red-border"><div class="kpi-title">Avg. Profit Margin</div><div class="kpi-value">{df_filtered['profit_margin'].mean():.2f}%</div></div>""", unsafe_allow_html=True)

best = df_filtered.loc[df_filtered["roas"].idxmax()]
worst = df_filtered.loc[df_filtered["roas"].idxmin()]
st.subheader(" Best & Worst Campaigns by ROAS")
st.markdown(f"**Best:** `{best['campaign']}` → **{best['roas']:.2f}**")
st.markdown(f"**Worst:** `{worst['campaign']}` → **{worst['roas']:.2f}**")

st.header(" Performance Over Time by Platform")
grouped = df_filtered.groupby(["date", "platform"])[["ad_spend", "sales"]].sum().reset_index()
fig_line = px.line(
    grouped,
    x="date",
    y=["ad_spend", "sales"],
    color="platform",
    markers=True,
    line_shape="spline",
    title="Ad Spend & Sales Over Time by Platform"
)
fig_line.update_layout(
    xaxis_title="Date",
    yaxis_title="Amount ($)",
    template="plotly_dark",
    legend_title="Metric",
)
st.plotly_chart(fig_line, use_container_width=True)

st.header("Net Profit per Campaign")
campaign_profit = df_filtered.groupby("campaign")["net_profit"].sum().reset_index()
fig_bar = px.bar(
    campaign_profit,
    x="campaign",
    y="net_profit",
    color="net_profit",
    title="Net Profit by Campaign",
    color_continuous_scale="Tealrose"
)
fig_bar.update_layout(
    xaxis_title="Campaign",
    yaxis_title="Net Profit ($)",
    template="plotly_dark"
)
st.plotly_chart(fig_bar, use_container_width=True)

st.header(" Gross Income vs Total Cost")
df_income_cost = df_filtered.groupby("campaign")[["gross_income", "total_cost"]].sum().reset_index()
fig_grouped = px.bar(
    df_income_cost.melt(id_vars="campaign", value_vars=["gross_income", "total_cost"]),
    x="campaign",
    y="value",
    color="variable",
    barmode="group",
    title="Gross Income vs Total Cost by Campaign",
    color_discrete_map={"gross_income": "#00cec9", "total_cost": "#d63031"}
)
fig_grouped.update_layout(
    xaxis_title="Campaign",
    yaxis_title="Amount ($)",
    template="plotly_dark"
)
st.plotly_chart(fig_grouped, use_container_width=True)

st.header("Full Campaign Data Overview")
st.dataframe(df_filtered.reset_index(drop=True), use_container_width=True)
csv_final = df_filtered.to_csv(index=False).encode("utf-8")
st.download_button("⬇ Download Final CSV", csv_final, "final_campaign_data.csv", "text/csv")
