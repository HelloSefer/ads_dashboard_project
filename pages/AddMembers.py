import streamlit as st
import mysql.connector
import os
from dotenv import load_dotenv 

load_dotenv()
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306))  # default 3306 if not found
    )


def load_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

def find_user(username):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def insert_user(username, password, role, admin, status="active"):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO users (username, password, role, admin, status)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (username, password, role, admin, status))
    conn.commit()
    cursor.close()
    conn.close()

def delete_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = %s", (username,))
    conn.commit()
    cursor.close()
    conn.close()

def update_user_status(username, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = %s WHERE username = %s", (status, username))
    conn.commit()
    cursor.close()
    conn.close()


if "username" not in st.session_state:
    st.warning("Please log in first.")
    st.stop()

if st.session_state.get("role") != "admin":
    st.error("You do not have permission to access this page.")
    st.stop()

st.title("🛡️ Team Control Panel")

tab1, tab2, tab3 = st.tabs(["Add Member", "Delete Member", "Activate/Deactivate Member"])

with tab1:
    st.subheader("Add a New Team Member")
    username = st.text_input("Username").strip().lower()
    password = st.text_input("Password", type="password").strip()

    if st.button("Register Member"):
        if not username or not password:
            st.warning("Please fill in all fields.")
        elif find_user(username) is not None:
            st.error("Username already exists.")
        else:
            insert_user(username, password, role="user", admin=st.session_state["username"])
            st.markdown(f"<div class='fly-success'>Member '{username}' added successfully!</div>", unsafe_allow_html=True)

with tab2:
    st.subheader("Remove a Team Member")
    users = load_users()
    usernames = [u["username"] for u in users if u["role"] == "user"]

    if usernames:
        selected_user = st.selectbox("Select User to Delete", usernames)
        confirm = st.checkbox("I confirm I want to delete this user")

        if st.button("Delete User"):
            if confirm:
                delete_user(selected_user)
                st.markdown(f"<div class='fly-success'>User '{selected_user}' has been deleted.</div>", unsafe_allow_html=True)
            else:
                st.warning("Please confirm before deleting.")
    else:
        st.info("No users available for deletion.")

with tab3:
    st.subheader("Activate or Deactivate a Member")
    users = load_users()
    members = [u for u in users if u["role"] == "user"]

    if members:
        selected_user = st.selectbox("Select User", [u["username"] for u in members])
        user_obj = find_user(selected_user)

        if user_obj:
            status = user_obj.get("status", "active")
            st.markdown(f"**Status:** {'🟢 Active' if status == 'active' else '🔴 Inactive'}")

            confirm = st.checkbox("Confirm status change")

            if status == "active":
                if st.button("Deactivate"):
                    if confirm:
                        update_user_status(selected_user, "inactive")
                        st.markdown(f"<div class='fly-success'>User '{selected_user}' has been deactivated.</div>", unsafe_allow_html=True)
                    else:
                        st.warning("Please confirm.")
            else:
                if st.button("Activate"):
                    if confirm:
                        update_user_status(selected_user, "active")
                        st.markdown(f"<div class='fly-success'>User '{selected_user}' has been activated.</div>", unsafe_allow_html=True)
                    else:
                        st.warning("Please confirm.")
    else:
        st.info("No users available to manage.")


st.markdown("""
<style>
body, .stApp {
    background: radial-gradient(circle at top left, #000000, #001f1f, #000000);
    color: #00ff00;
    font-family: 'Courier New', monospace;
}

/* Headers */
h1, h2, h3, .stSubheader {
    color: #00ff00;
    text-shadow: 0 0 15px #00ffcc;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #000000, #001a33);
    border-left: 3px solid #00ffff;
    box-shadow: 0 0 25px #00ffff, inset 0 0 15px #00ccff;
    animation: pulseGlow 4s infinite ease-in-out;
}
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 20px #00ffff, inset 0 0 15px #00ccff; }
    50% { box-shadow: 0 0 40px #ff0033, inset 0 0 25px #ff0033; }
}

/* Text inputs & password fields */
input, .stTextInput input, .stPasswordInput input {
    background-color: #000000;
    color: #00ffcc;
    border: 2px solid #00ff00;
    border-radius: 6px;
    padding: 0.4rem;
    font-size: 1rem;
}
input:focus {
    border-color: #ff0033;
    box-shadow: 0 0 10px #ff0033;
}

/* Selectbox dropdown and field */
div[data-baseweb="select"] {
    background-color: #000000;
    border: 2px solid #00ff00;
    border-radius: 6px;
    padding: 0.4rem;
    color: #00ffcc;
    font-family: 'Courier New', monospace;
    box-shadow: 0 0 8px #00ff00;
}
div[data-baseweb="select"]:hover {
    border-color: #ff0033;
    box-shadow: 0 0 15px #ff0033;
}

/* Dropdown options */
ul[role="listbox"] {
    background-color: #000000;
    border: 2px solid #00ff00;
}
li[role="option"] {
    color: #00ffff;
    padding: 0.5rem;
}
li[role="option"]:hover {
    background-color: #001a1a;
    color: #ffffff;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(45deg, #00ff00, #00ccff, #ff0033);
    border: none;
    color: black;
    font-weight: bold;
    padding: 0.6rem 1.4rem;
    border-radius: 10px;
    box-shadow: 0 0 15px #00ffcc;
    transition: all 0.3s ease-in-out;
}
.stButton > button:hover {
    transform: scale(1.07);
    box-shadow: 0 0 30px #ff0033;
    color: white;
}

/* Labels */
label, .stSelectbox label {
    color: #00ffff !important;
    font-weight: 600;
    text-shadow: 0 0 10px #00ffff;
}

/* Checkbox */
.stCheckbox {
    background-color: transparent;
    color: #00ffff;
    font-weight: 600;
}

/* Flying success message */
.fly-success {
    animation: flyAway 3s ease-in-out forwards;
    background: rgba(0, 255, 0, 0.1);
    color: #00ff00;
    border: 1px solid #00ff00;
    padding: 0.8rem;
    border-radius: 8px;
    font-weight: bold;
    margin-top: 1rem;
    text-align: center;
    box-shadow: 0 0 15px #00ff00;
    font-family: 'Courier New', monospace;
    position: relative;
    opacity: 1;
}
@keyframes flyAway {
    0%   { transform: translateY(0px); opacity: 1; }
    50%  { transform: translateY(-20px); opacity: 0.7; }
    100% { transform: translateY(-60px); opacity: 0; }
}
</style>
""", unsafe_allow_html=True)
