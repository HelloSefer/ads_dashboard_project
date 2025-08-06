
import streamlit as st
import pandas as pd
from datetime import date
import streamlit.components.v1 as components
import time
import threading
import mysql.connector
import os
from dotenv import load_dotenv 

load_dotenv()
if "username" not in st.session_state:
    st.warning("⚠️ Please login from the Home page.")
    st.stop()

username = st.session_state["username"]

if "campaign_added" not in st.session_state:
    st.session_state["campaign_added"] = False
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
.ballonat {
    position: fixed;
    bottom: -150px;
    animation: rise 8s linear infinite;
    opacity: 0.6;
    z-index: 0;
}
@keyframes rise {
    0% { transform: translateY(0) rotate(0deg); opacity: 0.5; }
    100% { transform: translateY(-1200px) rotate(360deg); opacity: 0; }
}
.ballonat::before {
    content: "🔶";
    font-size: 32px;
}
</style>
""", unsafe_allow_html=True)

for i in range(40):
    st.markdown(
        f"""<div class="ballonat" style="
            left: {i*2.5}% ;
            animation-delay: {i * 0.2}s;
            transition-delay: 0s;
        "></div>""", unsafe_allow_html=True)
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        ssl_ca=r"C:\ads_dashboard_project\ca.pem",  
        ssl_verify_cert=True
    )

st.header("Add New Campaign")

# 🧾 Form
with st.form("add_campaign_form"):
    col1, col2 = st.columns(2)
    with col1:
        platform = st.selectbox("Platform", ["facebook", "instagram", "tiktok", "google"])
        campaign = st.text_input("Campaign Name")
        camp_date = st.date_input("Date")
        product_cost = st.number_input("Product Cost per Unit", min_value=0.0, format="%.2f")
        units_sold = st.number_input("Units Sold", min_value=0, step=1)
    with col2:
        delivery_cost = st.number_input("Delivery Cost", min_value=0.0, format="%.2f")
        price_per_unit = st.number_input("Price per Unit", min_value=0.0, format="%.2f")
        ad_spend = st.number_input("Ad Spend", min_value=0.0, format="%.2f")
        clicks = st.number_input("Clicks", min_value=0, step=1)

    submitted = st.form_submit_button("Add Campaign")

if submitted:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        mysql_date = camp_date.strftime("%Y-%m-%d")

        cursor.execute("""
            INSERT INTO campaigns 
            (username, platform, date, campaign, ad_spend, clicks, product_cost, units_sold, delivery_cost, price_per_unit)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            username, platform, mysql_date, campaign, ad_spend, clicks, 
            product_cost, units_sold, delivery_cost, price_per_unit
        ))

        conn.commit()
        conn.close()

        st.session_state["campaign_added"] = True

    except Exception as e:
        st.error(f"❌ Error saving data: {e}")
        st.session_state["campaign_added"] = False

if st.session_state.get("campaign_added", False):
    st.success("✅ Campaign added successfully!")
    st.balloons()

    def clear_success():
        time.sleep(3)
        st.session_state["campaign_added"] = False

    threading.Thread(target=clear_success, daemon=True).start()

st.markdown("<div id='scroll-bottom'></div>", unsafe_allow_html=True)
components.html("""
<script>
    const el = window.parent.document.querySelector('#scroll-bottom');
    if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
    }
</script>
""", height=0)

