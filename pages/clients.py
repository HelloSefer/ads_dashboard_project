import streamlit as st
import pandas as pd
import mysql.connector
import folium
from streamlit_folium import folium_static
from fpdf import FPDF
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import plotly.express as px
import style
import os
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    port=int(os.getenv("DB_PORT", 3306))
)
cursor = conn.cursor(dictionary=True)


style.apply_custom_styles()

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
.purple-border { border-left: 6px solid #9b59b6; box-shadow: 0 0 10px #9b59b6; }
.kpi-title { font-size: 14px; color: #aaa; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-value { font-size: 26px; font-weight: bold; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

if "username" not in st.session_state:
    st.warning("Please log in from the main page.")
    st.stop()

username = st.session_state["username"].lower()
role = st.session_state.get("role", "").lower()

cursor.execute("SELECT * FROM users")
users_data = cursor.fetchall()
allowed_users = [u["username"] for u in users_data if u.get("admin") == username or u["username"] == username]

if username not in allowed_users:
    st.error("You are not allowed to access client data.")
    st.stop()

cursor.execute("SELECT * FROM clients")
df = pd.DataFrame(cursor.fetchall())

if df.empty:
    st.warning("No client data found.")
    st.stop()

df["username"] = df["username"].astype(str).str.lower()
df["city"] = df["city"].astype(str).str.strip().str.title()
df["created_at"] = pd.to_datetime(df["created_at"], errors='coerce')
df["lat"] = pd.to_numeric(df["lat"], errors='coerce')
df["lon"] = pd.to_numeric(df["lon"], errors='coerce')

missing_coords = df[df["lat"].isnull() | df["lon"].isnull()]
if not missing_coords.empty:
    st.warning("Generating missing coordinates...")
    geolocator = Nominatim(user_agent="client_dashboard")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    missing_coords["location"] = missing_coords["address"].astype(str) + ", " + missing_coords["city"].astype(str) + ", Morocco"

    def safe_geocode(loc):
        try:
            return geocode(loc)
        except:
            return None

    missing_coords["location_obj"] = missing_coords["location"].apply(safe_geocode)
    missing_coords["lat"] = missing_coords["location_obj"].apply(lambda loc: loc.latitude if loc else None)
    missing_coords["lon"] = missing_coords["location_obj"].apply(lambda loc: loc.longitude if loc else None)
    missing_coords.drop(columns=["location", "location_obj"], inplace=True)

    for idx, row in missing_coords.iterrows():
        df.loc[idx, "lat"] = row["lat"]
        df.loc[idx, "lon"] = row["lon"]

st.set_page_config(page_title="Client Management Dashboard", layout="wide")
st.title("Client Management Dashboard")

with st.sidebar:
    st.header("Filter Clients")
    if role == "admin":
        team_options = ["ALL"] + allowed_users
        selected_user = st.selectbox("Select team member to view clients:", team_options, index=0)
        filtered_df = df[df["username"].isin(allowed_users)] if selected_user == "ALL" else df[df["username"] == selected_user]
    else:
        filtered_df = df[df["username"] == username]

    gender = st.selectbox("Gender", ["All", "male", "female"])
    city = st.selectbox("City", ["All"] + sorted(filtered_df["city"].dropna().unique()))
    platform = st.selectbox("Preferred Platform", ["All"] + sorted(filtered_df["preferred_platform"].dropna().unique()))
    customer_type = st.selectbox("Customer Type", ["All"] + sorted(filtered_df["customer_type"].dropna().unique()))

    if gender != "All":
        filtered_df = filtered_df[filtered_df["gender"].str.lower() == gender]
    if city != "All":
        filtered_df = filtered_df[filtered_df["city"] == city]
    if platform != "All":
        filtered_df = filtered_df[filtered_df["preferred_platform"] == platform]
    if customer_type != "All":
        filtered_df = filtered_df[filtered_df["customer_type"] == customer_type]

st.subheader("Quick Stats")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="kpi-box blue-border"><div class="kpi-title">Total Clients</div><div class="kpi-value">{len(filtered_df)}</div></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="kpi-box red-border"><div class="kpi-title">Female</div><div class="kpi-value">{(filtered_df["gender"].str.lower() == "female").sum()}</div></div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="kpi-box green-border"><div class="kpi-title">Male</div><div class="kpi-value">{(filtered_df["gender"].str.lower() == "male").sum()}</div></div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="kpi-box purple-border"><div class="kpi-title">Unique Cities</div><div class="kpi-value">{filtered_df["city"].nunique()}</div></div>""", unsafe_allow_html=True)

st.subheader("Client Registration Timeline")
timeline = filtered_df.groupby(filtered_df["created_at"].dt.date).size()
st.line_chart(timeline)

st.subheader("Visual Charts")
col1, col2 = st.columns(2)

with col1:
    platform_data = filtered_df["preferred_platform"].fillna("Unknown").value_counts().reset_index(name="count")
    platform_data.columns = ["preferred_platform", "count"]
    fig1 = px.bar(platform_data, x="preferred_platform", y="count", color="preferred_platform", title="Preferred Platforms")
    st.plotly_chart(fig1, use_container_width=True)

    type_data = filtered_df["customer_type"].fillna("Unknown").value_counts().reset_index(name="count")
    type_data.columns = ["customer_type", "count"]
    fig2 = px.pie(type_data, names="customer_type", values="count", title="Customer Types Distribution")
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    gender_data = filtered_df["gender"].fillna("Unknown").value_counts().reset_index(name="count")
    gender_data.columns = ["gender", "count"]
    fig3 = px.pie(gender_data, names="gender", values="count", title="Gender Distribution")
    st.plotly_chart(fig3, use_container_width=True)

    city_data = filtered_df["city"].fillna("Unknown").value_counts().nlargest(10).reset_index(name="count")
    city_data.columns = ["city", "count"]
    fig4 = px.bar(city_data, x="city", y="count", color="city", title="Top 10 Cities")
    st.plotly_chart(fig4, use_container_width=True)

st.subheader("Clients Map")
map_df = filtered_df.dropna(subset=["lat", "lon"])
if not map_df.empty:
    m = folium.Map(location=[map_df["lat"].mean(), map_df["lon"].mean()], zoom_start=6)
    city_counts = map_df["city"].value_counts()
    max_count = city_counts.max()

    def get_marker_color(count):
        if count == max_count:
            return "red"
        elif count >= 0.7 * max_count:
            return "orange"
        else:
            return "blue"

    for city_name, count in city_counts.items():
        city_data = map_df[map_df["city"] == city_name]
        avg_lat = city_data["lat"].mean()
        avg_lon = city_data["lon"].mean()
        percentage = round((count / max_count) * 100)

        popup_html = f"""<div style='font-size:14px'><b>City:</b> {city_name}<br><b>Clients:</b> {count}<br><b>Relative Share:</b> {percentage}%</div>"""

        folium.Marker(
            location=[avg_lat, avg_lon],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{city_name} - {count} clients",
            icon=folium.Icon(color=get_marker_color(count), icon="user")
        ).add_to(m)

        folium.CircleMarker(
            location=[avg_lat, avg_lon],
            radius=5 + (count / max_count) * 20,
            color=get_marker_color(count),
            fill=True,
            fill_opacity=0.2,
            popup=folium.Popup(popup_html, max_width=250)
        ).add_to(m)

    folium_static(m, width=800, height=550)
else:
    st.info("Not enough data to display the map.")

st.subheader("Clients Table")
st.dataframe(filtered_df.drop(columns=["user_id", "lat", "lon"], errors="ignore"), use_container_width=True)

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Client Report", 0, 1, "C")
        self.ln(5)

def generate_pdf(dataframe):
    pdf = PDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font("Arial", size=6)
    dataframe = dataframe.drop(columns=["user_id", "lat", "lon"], errors="ignore")

    col_widths = {
        "username": 22, "full_name": 32, "gender": 12, "age": 10,
        "city": 20, "address": 40, "phone": 28, "email": 40,
        "preferred_platform": 22, "preferred_product_type": 25,
        "customer_type": 18, "created_at": 22
    }

    headers = list(dataframe.columns)
    for col in headers:
        pdf.cell(col_widths.get(col, 20), 8, str(col), border=1, align='C')
    pdf.ln()

    for _, row in dataframe.iterrows():
        for col in headers:
            text = str(row[col])
            pdf.cell(col_widths.get(col, 20), 7, text, border=1, align='C')
        pdf.ln()

    return bytes(pdf.output(dest='S'))

st.subheader("⬇ Download Client Data")
csv_data = filtered_df.drop(columns=["user_id", "lat", "lon"], errors="ignore").to_csv(index=False).encode("utf-8")
pdf_data = generate_pdf(filtered_df)

col1, col2 = st.columns(2)
with col1:
    st.download_button("⬇ Download CSV", data=csv_data, file_name="clients.csv", mime="text/csv")
with col2:
    st.download_button("⬇ Download PDF", data=pdf_data, file_name="clients.pdf", mime="application/pdf")

cursor.close()
conn.close()
