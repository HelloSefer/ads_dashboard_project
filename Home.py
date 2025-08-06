import streamlit as st
import random
import os  
import mysql.connector
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from dotenv import load_dotenv 

load_dotenv()
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# ✅ Brevo API setup
BREVO_API_KEY = os.getenv("BREVO_API_KEY")  
SENDER_EMAIL = "oussamabillionaire599@gmail.com"
SENDER_NAME = "ANA9A STORE"

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = BREVO_API_KEY
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


def send_verification_code(email, code):
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        sender={"name": SENDER_NAME, "email": SENDER_EMAIL},
        to=[{"email": email}],
        subject="Your Verification Code",
        html_content=f"<h2>Welcome!</h2><p>Your verification code is: <b style='font-size:22px;'>{code}</b></p>"
    )
    try:
        api_instance.send_transac_email(send_smtp_email)
        return True
    except ApiException as e:
        st.error(f"Error while sending code: {e}")
        return False


def load_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

def find_user_by_email_or_username(identifier):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM users WHERE LOWER(email) = %s OR LOWER(username) = %s"
    cursor.execute(query, (identifier.lower(), identifier.lower()))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def find_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM users WHERE LOWER(email) = %s"
    cursor.execute(query, (email.lower(),))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def insert_user(email, username, password, role="admin", admin=None, status="active"):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO users (email, username, password, role, admin, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (email, username, password, role, admin if admin else username, status))
    conn.commit()
    cursor.close()
    conn.close()

def update_user_password(email, new_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "UPDATE users SET password = %s WHERE LOWER(email) = %s"
    cursor.execute(query, (new_password, email.lower()))
    conn.commit()
    cursor.close()
    conn.close()


st.set_page_config(page_title="ANA9A STORE", initial_sidebar_state="collapsed")
st.markdown('<div class="title-fire">🔥 ANA9A STORE 🔥</div>', unsafe_allow_html=True)

tab_login, tab_signup = st.tabs(["Login", "Create New Account"])

with tab_login:

    if "show_reset" not in st.session_state:
        st.session_state["show_reset"] = False
    if "code_sent" not in st.session_state:
        st.session_state["code_sent"] = False

    if not st.session_state["show_reset"]:
        st.header("Login")
    else:
        st.header("Reset Your Password")

    if not st.session_state["show_reset"]:
        login_input = st.text_input("Email or Username", key="login_input").strip().lower()
        password_login = st.text_input("Password", type="password", key="login_password").strip()

        if st.button("Login"):
            user = find_user_by_email_or_username(login_input)
            if user and user["password"] == password_login:
                if user.get("status", "active") == "inactive":
                    st.error("Your account has been deactivated by the administrator. Please contact the management")
                else:
                    st.session_state["username"] = user["username"]
                    st.session_state["role"] = user["role"]
                    st.session_state["admin"] = user.get("admin", None)
                    st.success(f"Welcome {user['username']}!")
                    st.switch_page("pages/Dashboard.py")
            else:
                st.error("Incorrect email/username or password")

        if st.button("Forgot Password?"):
            st.session_state["show_reset"] = True

    else:
        forgot_email = st.text_input("Enter your registered email").strip().lower()

        if not st.session_state["code_sent"]:
            if st.button("Send Reset Code"):
                user = find_user_by_email(forgot_email)
                if not user:
                    st.error("This email is not registered")
                else:
                    reset_code = str(random.randint(100000, 999999))
                    st.session_state["reset_code"] = reset_code
                    st.session_state["reset_email"] = forgot_email
                    sent = send_verification_code(forgot_email, reset_code)
                    if sent:
                        st.session_state["code_sent"] = True
                        st.success("Code sent to your email")
                        st.rerun()

        if st.session_state["code_sent"]:
            entered_code = st.text_input("Enter the code").strip()
            new_pass = st.text_input(" New Password", type="password")
            confirm_pass = st.text_input(" Confirm New Password", type="password")

            if st.button("Reset Password"):
                if entered_code != st.session_state["reset_code"]:
                    st.error("Incorrect code")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match")
                elif not new_pass:
                    st.error("Please enter a new password")
                else:
                    update_user_password(st.session_state["reset_email"], new_pass)
                    st.success("Password reset successfully! Please log in.")
                    st.session_state["show_reset"] = False
                    st.session_state["code_sent"] = False
                    del st.session_state["reset_code"]
                    del st.session_state["reset_email"]

        if st.button("Back to Login"):
            st.session_state["show_reset"] = False
            st.session_state["code_sent"] = False
            st.session_state.pop("reset_code", None)
            st.session_state.pop("reset_email", None)

with tab_signup:
    st.header("Create New Account")

    if "email_verified" not in st.session_state:
        st.session_state["email_verified"] = False
    if "verification_code" not in st.session_state:
        st.session_state["verification_code"] = None
    if "temp_email" not in st.session_state:
        st.session_state["temp_email"] = None

    if not st.session_state["email_verified"]:
        email_signup = st.text_input("Email", key="signup_email").strip().lower()

        if st.button("Send Verification Code"):
            if not email_signup:
                st.warning("Please enter your email")
            elif find_user_by_email(email_signup):
                st.error("This email is already used")
            else:
                code = random.randint(100000, 999999)
                sent = send_verification_code(email_signup, code)
                if sent:
                    st.session_state["verification_code"] = str(code)
                    st.session_state["temp_email"] = email_signup
                    st.info("Verification code sent to your email")
                    st.rerun()

        if st.session_state["verification_code"]:
            code_input = st.text_input("Enter verification code")
            if st.button("Verify Code"):
                if code_input == st.session_state["verification_code"]:
                    st.session_state["email_verified"] = True
                    st.success("Email verified successfully!")
                    st.rerun()
                else:
                    st.error("Incorrect code")

    if st.session_state["email_verified"]:
        username_signup = st.text_input("Username").strip().lower()
        password_signup = st.text_input("Password", type="password").strip()
        confirm_password_signup = st.text_input("Confirm Password", type="password").strip()

        if st.button("🆕 Create Account"):
            if not username_signup or not password_signup or not confirm_password_signup:
                st.warning("⚠️ Please fill all the fields")
            else:
                existing_user = find_user_by_email_or_username(username_signup)
                if existing_user:
                    st.error("Username or email is already taken")
                elif password_signup != confirm_password_signup:
                    st.error("Passwords do not match")
                else:
                    insert_user(st.session_state["temp_email"], username_signup, password_signup, role="admin", admin=username_signup)
                    st.success("✅ Account created successfully! You can now log in.")
                    st.session_state["email_verified"] = False
                    st.session_state["verification_code"] = None
                    st.session_state["temp_email"] = None
                    st.rerun()

                
st.markdown("""
        <style>
            [data-testid="stSidebarNav"] ul li:nth-child(n+2) {
                display: none !important;
            }
            [data-testid="stSidebar"] { display: block !important; }
        </style>
    """, unsafe_allow_html=True)


st.markdown("""<style>
body { background: #000010; overflow: hidden; }
.stApp {
  position: relative;
  background: radial-gradient(ellipse at bottom, #0b0c29 0%, #000010 80%);
  min-height: 100vh;
  overflow: hidden;
}
@keyframes twinkle {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.star {
  position: absolute;
  background: white;
  border-radius: 50%;
  opacity: 0.8;
  animation: twinkle 3s infinite ease-in-out;
}
.star:nth-child(1) { top: 10%; left: 20%; width: 3px; height: 3px; animation-delay: 0s; }
.star:nth-child(2) { top: 30%; left: 70%; width: 2px; height: 2px; animation-delay: 1s; }
.star:nth-child(3) { top: 60%; left: 40%; width: 4px; height: 4px; animation-delay: 2s; }
.star:nth-child(4) { top: 80%; left: 80%; width: 1.5px; height: 1.5px; animation-delay: 0.5s; }

@keyframes flicker {
  0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% {
    text-shadow: 0 0 5px #ff6f00, 0 0 10px #ff6f00,
                 0 0 20px #ff6f00, 0 0 40px #ff3d00,
                 0 0 80px #ff3d00, 0 0 90px #ff3d00,
                 0 0 100px #ff3d00, 0 0 150px #ff3d00;
  }
  20%, 22%, 24%, 55% { text-shadow: none; }
}
@keyframes slow-rotate {
  0% { transform: rotate(0deg);}
  50% { transform: rotate(3deg);}
  100% { transform: rotate(0);}
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
.title-fire {
  font-size: 3rem;
  font-weight: 900;
  color: #ff4500;
  text-align: center;
  animation: flicker 3s infinite, slow-rotate 6s infinite ease-in-out;
  user-select: none;
  margin-bottom: 2rem;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.input-container {
  max-width: 350px;
  margin: 0 auto;
  animation: slideUp 1s ease forwards;
}
.stTextInput > label, .stTextInput > div > label {
  color: #ffa500;
  font-weight: 700;
  font-size: 1.2rem;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  margin-bottom: 0.5rem;
  display: block;
  user-select: none;
  text-shadow: 0 0 5px rgba(255, 165, 0, 0.7);
  transition: color 0.3s ease, text-shadow 0.3s ease;
  cursor: default;
}
.stTextInput > label:hover, .stTextInput > div > label:hover {
  color: #ffcc66;
  text-shadow: 0 0 12px rgba(255, 204, 102, 0.9);
}
input[type="text"], input[type="password"] {
  width: 100%;
  padding: 0.8rem 1rem 0.8rem 2.5rem;
  border: 2px solid #ff6f00;
  border-radius: 12px;
  font-size: 1.1rem;
  background-color: #3a0a00;
  color: #fff;
  transition: 0.3s ease;
  background-repeat: no-repeat;
  background-position: 10px center;
}
input[type="text"]:focus, input[type="password"]:focus {
  outline: none;
  background-color: #4a0f00;
  border-color: #ff3d00;
  box-shadow: 0 0 12px 2px #ff4500;
}
input[type="text"] { background-image: url("https://img.icons8.com/ios-filled/24/ff6f00/user.png"); }
input[type="password"] { background-image: url("https://img.icons8.com/ios-filled/24/ff6f00/lock.png"); }

.stButton button {
  background: linear-gradient(135deg, #ff6f00, #ff3d00) !important;
  color: #fff !important;
  font-size: 1.2rem !important;
  font-weight: bold !important;
  padding: 0.75rem 1rem !important;
  border: none !important;
  border-radius: 40px !important;
  width: 100% !important;
  box-shadow: 0 0 15px #ff6f00;
  cursor: pointer;
  transition: all 0.3s ease-in-out;
}
.stButton button:hover {
  animation: smoke 1s ease-in-out;
  transform: scale(1.05);
  background: linear-gradient(135deg, #ff3d00, #ff6f00);
  box-shadow: 0 0 30px #ff8c00, 0 0 55px #ff4500;
}
@keyframes smoke {
  0% { box-shadow: 0 0 15px #ff6f00; }
  50% {
    box-shadow: 0 0 35px 15px rgba(255, 140, 0, 0.5),
                0 0 60px 30px rgba(255, 69, 0, 0.3);
    transform: scale(1.05);
  }
  100% { box-shadow: 0 0 15px #ff6f00; transform: scale(1); }
}
[data-testid="stSidebar"] {
  background: linear-gradient(135deg, #3a0a00, #5a1a00);
  box-shadow: inset 0 0 20px #ff3d00, 0 0 30px #ff6f00;
  border-radius: 10px;
  color: #ffbb80 !important;
  font-weight: 600;
}
[data-testid="stSidebar"]:hover {
  box-shadow: inset 0 0 40px #ff4500, 0 0 60px #ff8c00;
  transform: scale(1.02);
}
[data-testid="stSidebar"] ::-webkit-scrollbar { width: 8px; }
[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
  background: #ff3d00;
  border-radius: 4px;
}
span[aria-live="polite"] {
  display: none !important;
  visibility: hidden !important;
  font-size: 0px !important;
}
</style>""", unsafe_allow_html=True)
st.markdown("""
<div class="star"></div>
<div class="star"></div>
<div class="star"></div>
<div class="star"></div>
""", unsafe_allow_html=True)