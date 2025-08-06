import streamlit as st
import mysql.connector
from datetime import datetime
import uuid
import os
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from dotenv import load_dotenv 

load_dotenv()
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

IMAGE_FOLDER = "chat_images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

def save_uploaded_image(uploaded_file):
    if uploaded_file is None:
        return None
    extension = uploaded_file.name.split(".")[-1]
    filename = f"{uuid.uuid4()}.{extension}"
    filepath = os.path.join(IMAGE_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath

def load_chats():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM chat ORDER BY timestamp ASC")
    chats = cursor.fetchall()

    for chat in chats:
        cursor.execute(
            "SELECT name, message, timestamp FROM chat_replies WHERE chat_id = %s ORDER BY timestamp ASC",
            (chat["id"],)
        )
        chat["replies"] = cursor.fetchall()

    cursor.close()
    conn.close()
    return chats

def insert_chat(username, text, image_path=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    chat_id = str(uuid.uuid4())
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    query = """
        INSERT INTO chat (id, username, timestamp, text, image_path, edited_timestamp)
        VALUES (%s, %s, %s, %s, %s, NULL)
    """
    cursor.execute(query, (chat_id, username, now, text, image_path))
    conn.commit()
    cursor.close()
    conn.close()

def add_reply(chat_id, replier, reply_text):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    query = """
        INSERT INTO chat_replies (chat_id, name, message, timestamp)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (chat_id, replier, reply_text, now))
    conn.commit()
    cursor.close()
    conn.close()

def delete_chat(chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_replies WHERE chat_id = %s", (chat_id,))
    cursor.execute("DELETE FROM chat WHERE id = %s", (chat_id,))
    conn.commit()
    cursor.close()
    conn.close()

def display_message(msg, current_user):
    sender_raw = msg.get("username", "Unknown")
    sender_display = "You" if sender_raw == current_user else sender_raw
    timestamp = msg.get("timestamp", "")
    text = msg.get("text", "")
    image_path = msg.get("image_path")

    with st.container():
        st.markdown(f"**{sender_display}** ~ {timestamp}")
        if text:
            st.write(text)

        if image_path and os.path.exists(image_path):
            st.image(image_path, width=150, caption="Click to view full image")
            with st.expander(" View full image"):
                st.image(image_path, use_container_width=True)
                with open(image_path, "rb") as img_file:
                    st.download_button("⬇ Download Image", img_file, file_name=os.path.basename(image_path))

        if msg.get("replies"):
            for reply in msg["replies"]:
                st.markdown(
                    f"""
                    <div style="
                        margin-left: 40px; 
                margin-bottom: 8px; 
                background-color: #220033;  /* deep violet bg */
                padding: 10px 15px; 
                border-radius: 15px 15px 15px 0; 
                max-width: 70%; 
                font-size: 14px;
                box-shadow: 0 2px 6px rgba(139, 233, 253, 0.5); /* cyan glow */
                color: #8be9fd; /* neon cyan text */
                font-family: 'Courier New', monospace;
                ">
                <b style='color:#bd93f9;'>{reply['name']}</b> 
                <span style='font-size:10px; color:#ff79c6; margin-left: 10px;'>{reply['timestamp']}</span>
                <div style="margin-top:5px; white-space: pre-wrap; color:#f8f8f2;">{reply['message']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with st.expander("Reply", expanded=False):
            with st.form(f"reply_form_{msg['id']}", clear_on_submit=True):
                reply_text = st.text_area("Reply message", max_chars=300, key=f"reply_text_{msg['id']}")
                reply_submit = st.form_submit_button("Send Reply")
                if reply_submit and reply_text.strip():
                    add_reply(msg["id"], current_user, reply_text.strip())
                    st.rerun()

        if sender_raw == current_user:
            if st.button("delete message", key=f"delete_{msg['id']}"):
                return msg['id']

        st.markdown("---")
    return None

st.set_page_config(page_title="Team Chat", layout="wide")
st.title("💬 Team Chat")

st_autorefresh(interval=3000, key="chat_refresh")

if "username" not in st.session_state:
    st.session_state["username"] = "Guest"
username = st.session_state["username"]

messages = load_chats()

with st.sidebar.form("message_form", clear_on_submit=True):
    message_text = st.text_area("Message Text", max_chars=500)
    uploaded_image = st.file_uploader("", type=["png", "jpg", "jpeg", "gif"])
    send = st.form_submit_button("Send")

    if send:
        if not message_text.strip() and uploaded_image is None:
            st.sidebar.warning("⚠ Please write a message or attach an image.")
        else:
            image_path = save_uploaded_image(uploaded_image)
            insert_chat(username, message_text.strip(), image_path)
            st.sidebar.success("Message sent successfully.")
            st.rerun()

chat_container = st.container()
scroll_target = st.empty()
message_to_delete = None

with chat_container:
    for msg in messages:
        deleted_id = display_message(msg, username)
        if deleted_id:
            message_to_delete = deleted_id

scroll_target.markdown("<div id='last'></div>", unsafe_allow_html=True)

components.html("""
<script>
    const el = window.parent.document.querySelector('#last');
    if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
    }
</script>
""", height=0)

if message_to_delete:
    delete_chat(message_to_delete)
    st.rerun()






st.markdown("""
<style>
body, .stApp {
    background: radial-gradient(circle at top left, #1a0033, #000015, #000000);
    color: #8be9fd;
    font-family: 'Courier New', monospace;
}

/* Headers */
h1, h2, h3, .stSubheader {
    color: #bd93f9;
    text-shadow: 0 0 12px #ff79c6;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #0d001a, #220033);
    border-left: 3px solid #bd93f9;
    box-shadow: 0 0 25px #8be9fd, inset 0 0 15px #bd93f9;
    animation: pulseGlow 4s infinite ease-in-out;
}
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 20px #bd93f9, inset 0 0 15px #8be9fd; }
    50% { box-shadow: 0 0 40px #ff79c6, inset 0 0 25px #ff79c6; }
}

/* Text inputs & password fields */
input, .stTextInput input, .stPasswordInput input {
    background-color: #0d001a;
    color: #f8f8f2;
    border: 2px solid #bd93f9;
    border-radius: 6px;
    padding: 0.4rem;
    font-size: 1rem;
}
input:focus {
    border-color: #ff79c6;
    box-shadow: 0 0 10px #ff79c6;
}

/* Selectbox dropdown and field */
div[data-baseweb="select"] {
    background-color: #0d001a;
    border: 2px solid #bd93f9;
    border-radius: 6px;
    padding: 0.4rem;
    color: #f8f8f2;
    font-family: 'Courier New', monospace;
    box-shadow: 0 0 8px #bd93f9;
}
div[data-baseweb="select"]:hover {
    border-color: #ff79c6;
    box-shadow: 0 0 15px #ff79c6;
}

/* Dropdown options */
ul[role="listbox"] {
    background-color: #0d001a;
    border: 2px solid #bd93f9;
}
li[role="option"] {
    color: #8be9fd;
    padding: 0.5rem;
}
li[role="option"]:hover {
    background-color: #220033;
    color: #ffffff;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(45deg, #bd93f9, #8be9fd, #ff79c6);
    border: none;
    color: #0d001a;
    font-weight: bold;
    padding: 0.6rem 1.4rem;
    border-radius: 10px;
    box-shadow: 0 0 15px #8be9fd;
    transition: all 0.3s ease-in-out;
}
.stButton > button:hover {
    transform: scale(1.07);
    box-shadow: 0 0 30px #ff79c6;
    color: white;
}

/* Labels */
label, .stSelectbox label {
    color: #bd93f9 !important;
    font-weight: 600;
    text-shadow: 0 0 10px #8be9fd;
}

/* Checkbox */
.stCheckbox {
    background-color: transparent;
    color: #8be9fd;
    font-weight: 600;
}

/* Flying success message */
.fly-success {
    animation: flyAway 3s ease-in-out forwards;
    background: rgba(189, 147, 249, 0.1);
    color: #bd93f9;
    border: 1px solid #bd93f9;
    padding: 0.8rem;
    border-radius: 8px;
    font-weight: bold;
    margin-top: 1rem;
    text-align: center;
    box-shadow: 0 0 15px #bd93f9;
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
