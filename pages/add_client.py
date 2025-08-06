import streamlit as st
import mysql.connector
from datetime import date
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import os
from dotenv import load_dotenv 

load_dotenv()
st.set_page_config(page_title="Manage Clients", layout="centered")

if "username" not in st.session_state:
    st.warning("Please login from the Home page.")
    st.stop()

st.title("Manage Clients")

def get_env_var(key):
    return st.secrets[key] if key in st.secrets else os.getenv(key)

def get_db_connection():
    return mysql.connector.connect(
        host=get_env_var("DB_HOST"),
        port=int(get_env_var("DB_PORT")),
        user=get_env_var("DB_USER"),
        password=get_env_var("DB_PASSWORD"),
        database=get_env_var("DB_NAME"),
        ssl_ca="certs/ca.pem",  # تأكد وجود الملف في هذا المسار داخل مشروعك
        ssl_verify_cert=True
    )

geolocator = Nominatim(user_agent="client_dashboard")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

balloons_css = """
<style>
@keyframes rise {
  0% { bottom: -150px; opacity: 0; transform: translateY(0) scale(0.5); }
  50% { opacity: 1; }
  100% { bottom: 110vh; opacity: 0; transform: translateY(-100px) scale(1.2); }
}
.balloon {
  position: fixed;
  bottom: -150px;
  border-radius: 50% / 60%;
  opacity: 0;
  animation-name: rise;
  animation-timing-function: ease-in-out;
  animation-iteration-count: 1;
  animation-fill-mode: forwards;
  width: 80px;
  height: 110px;
  filter: drop-shadow(0 0 6px rgba(0,0,0,0.2));
  box-shadow: 0 0 50px rgba(255,255,255,0.3);
}
""" + "\n".join([
    f".balloon{i} {{ background: radial-gradient(circle at 50% 30%, #{hex(0x100000 + i*9000)[2:]:0<6}, #{hex(0xFF0000 - i*5000)[2:]:0<6}); left: {3*i + 2}%; animation-duration: 3s; animation-delay: {round(i * 0.1, 2)}s; }}"
    for i in range(1, 29)
]) + "</style>"
st.markdown(balloons_css, unsafe_allow_html=True)

def load_clients():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM clients")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def save_client(data, is_update=False, client_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if is_update:
        query = """
            UPDATE clients SET
                full_name=%s, gender=%s, age=%s, city=%s, address=%s,
                phone=%s, email=%s, preferred_platform=%s, preferred_product_type=%s,
                customer_type=%s, created_at=%s, lat=%s, lon=%s
            WHERE id=%s
        """
        values = (
            data["full_name"], data["gender"], data["age"], data["city"], data["address"],
            data["phone"], data["email"], data["preferred_platform"], data["preferred_product_type"],
            data["customer_type"], data["created_at"], data["lat"], data["lon"], client_id
        )
    else:
        query = """
            INSERT INTO clients (
                user_id, username, full_name, gender, age, city, address, phone, email,
                preferred_platform, preferred_product_type, customer_type, created_at, lat, lon
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data["user_id"], data["username"], data["full_name"], data["gender"], data["age"],
            data["city"], data["address"], data["phone"], data["email"], data["preferred_platform"],
            data["preferred_product_type"], data["customer_type"], data["created_at"], data["lat"], data["lon"]
        )
    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()

def delete_client(client_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clients WHERE id = %s", (client_id,))
    conn.commit()
    cursor.close()
    conn.close()

clients = load_clients()
df = clients if clients else []
client_deleted = False

action = st.sidebar.selectbox("Action", ["Add New Client", "Edit Existing Client", "Delete Client"])
selected_row = None
selected_index = None

user_clients = [row for row in df if row["username"] == st.session_state["username"]] if st.session_state["username"] != "oussama" else df

if action in ["Edit Existing Client", "Delete Client"]:
    if not user_clients:
        st.warning("No clients available for this user.")
        st.stop()
    options = {f'{c["full_name"]} ({c["email"]})': c for c in user_clients}
    selected_label = st.selectbox("Select Client", list(options.keys()))
    selected_row = options[selected_label]
    selected_index = selected_row["id"]

    if action == "Delete Client":
        if st.button("Confirm Delete"):
            delete_client(selected_index)
            client_deleted = True
            st.success("✅ Client deleted successfully.")

if not client_deleted:
    with st.form("client_form"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name", value=selected_row["full_name"] if selected_row else "")
            age = st.number_input("Age", min_value=10, max_value=100, value=int(selected_row["age"]) if selected_row else 25)
            city = st.text_input("City", value=selected_row["city"] if selected_row else "")
            phone = st.text_input("Phone", value=selected_row["phone"] if selected_row else "")
            preferred_platform = st.selectbox(
                "Preferred Platform",
                ["facebook", "instagram", "tiktok", "google", "other"],
                index=["facebook", "instagram", "tiktok", "google", "other"].index(selected_row["preferred_platform"]) if selected_row else 0
            )
            customer_type = st.selectbox(
                "Customer Type",
                ["new", "returning"],
                index=["new", "returning"].index(selected_row["customer_type"]) if selected_row else 0
            )
        with col2:
            gender = st.selectbox("Gender", ["male", "female"], index=["male", "female"].index(selected_row["gender"]) if selected_row else 0)
            address = st.text_input("Address", value=selected_row["address"] if selected_row else "")
            email = st.text_input("Email", value=selected_row["email"] if selected_row else "")
            preferred_product_type = st.text_input("Preferred Product", value=selected_row["preferred_product_type"] if selected_row else "")
            created_at = st.date_input("Created At", value=selected_row["created_at"] if selected_row else date.today())

        submit_btn = st.form_submit_button("Save Client")

        if submit_btn:
            if not full_name.strip() or not email.strip() or not phone.strip():
                st.error("Full name, email, and phone are required.")
            else:
                lat, lon = (selected_row["lat"], selected_row["lon"]) if selected_row else ("", "")

                if selected_row is None:
                    location = geocode(city)
                    if location:
                        lat = location.latitude
                        lon = location.longitude

                new_data = {
                    "user_id": selected_row["user_id"] if selected_row else st.session_state["username"],
                    "username": selected_row["username"] if selected_row else st.session_state["username"],
                    "full_name": full_name.strip(),
                    "gender": gender,
                    "age": age,
                    "city": city.strip(),
                    "address": address.strip(),
                    "phone": phone.strip(),
                    "email": email.strip(),
                    "preferred_platform": preferred_platform,
                    "preferred_product_type": preferred_product_type.strip(),
                    "customer_type": customer_type,
                    "created_at": created_at.strftime("%Y-%m-%d"),
                    "lat": lat,
                    "lon": lon
                }

                if selected_row:
                    save_client(new_data, is_update=True, client_id=selected_index)
                    st.success("Client updated successfully!")
                else:
                    save_client(new_data)
                    st.success("Client added successfully!")

                balloons_html = "\n".join([f'<div class="balloon balloon{i}"></div>' for i in range(1, 29)]) + """
                <script>
                    setTimeout(function() {
                        const balloons = document.querySelectorAll('.balloon');
                        balloons.forEach(el => el.remove());
                    }, 3000);
                </script>
                """
                st.markdown(balloons_html, unsafe_allow_html=True)




st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #003366, #4a0f00);
    box-shadow: inset 0 0 25px #9c27b0, 0 0 40px #29b6f6;
    border-radius: 10px;
    color: #ffffff;
    animation: glowSidebar 4s ease-in-out infinite;
}
@keyframes glowSidebar {
    0%, 100% { box-shadow: inset 0 0 25px #9c27b0, 0 0 30px #29b6f6; }
    50% { box-shadow: inset 0 0 35px #29b6f6, 0 0 50px #ba68c8; }
}
[data-testid="stSidebar"] label {
    font-weight: bold;
    color: #d1c4e9;
}
[data-testid="stSidebar"] ::-webkit-scrollbar {
    width: 8px;
}
[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
    background: #29b6f6;
    border-radius: 4px;
}
body, .stApp {
    background: linear-gradient(135deg, #001a33, #0d0029);
    color: #ddd;
    font-family: 'Segoe UI', sans-serif;
}
h1, h2, h3 {
    color: #b388ff;
    text-shadow: 0 0 8px #9575cd;
}
[data-testid="stForm"] {
    background-color: rgba(20, 12, 40, 0.75);
    border: 2px solid #7e57c2;
    border-radius: 15px;
    padding: 2rem;
    box-shadow: 0 0 20px #7e57c2cc;
    backdrop-filter: blur(8px);
    transition: box-shadow 0.3s ease;
}
[data-testid="stForm"]:hover, [data-testid="stForm"]:focus-within {
    box-shadow: 0 0 30px #9575cddd;
}
input[type="text"], input[type="number"], input[type="email"], input[type="date"] {
    background-color: #1a1333;
    color: #ddd;
    border: 2px solid #9575cd;
    border-radius: 8px;
    padding: 0.5rem;
    font-size: 1rem;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
input[type="text"]:focus, input[type="number"]:focus, input[type="email"]:focus, input[type="date"]:focus {
    outline: none;
    border-color: #b388ff;
    box-shadow: 0 0 8px #b388ffaa;
}
.stButton > button {
    background: linear-gradient(90deg, #7e57c2, #9575cd);
    border: none;
    color: white;
    padding: 0.7rem 1.5rem;
    border-radius: 25px;
    font-weight: bold;
    font-size: 1rem;
    box-shadow: 0 0 15px #9575cdcc;
    transition: background 0.3s ease, box-shadow 0.3s ease, transform 0.3s ease;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #b388ff, #d1c4e9);
    box-shadow: 0 0 25px #d1c4e9dd;
    transform: scale(1.05);
}
label {
    color: #d1c4e9 !important;
    font-weight: 600;
    font-size: 1.05rem;
    text-shadow: 0 0 4px #9575cd;
}
.stSelectbox > div[data-baseweb="select"] {
    background-color: #1a1333;
    color: #ddd;
    border: 2px solid #9575cd;
    border-radius: 8px;
    padding: 4px;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.stSelectbox > div[data-baseweb="select"]:hover {
    border-color: #b388ff;
    box-shadow: 0 0 8px #b388ffaa;
}
.stSelectbox label {
    color: #d1c4e9 !important;
    font-weight: 600;
    font-size: 1.05rem;
    text-shadow: 0 0 4px #9575cd;
}
</style>
""", unsafe_allow_html=True)