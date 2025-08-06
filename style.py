import streamlit as st

def apply_custom_styles():

    
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
