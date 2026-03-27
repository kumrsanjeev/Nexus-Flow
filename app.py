import streamlit as st
from agent import initialize_agent, get_chat_response
from tools import get_system_status

# 1. Page Config
st.set_page_config(
    page_title="Nexus Flow AI", 
    page_icon="⚡", 
    layout="wide"
)

# 2. Custom CSS for better styling
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stChatMessage { border-radius: 15px; border: 1px solid #161B22; }
    </style>
    """, unsafe_allow_html=True) # ✅ Corrected

# 3. Sidebar - Branding & Controls
with st.sidebar:
    st.image("https://img.icons8.com/nolan/512/artificial-intelligence.png", width=100)
    st.title("Nexus Flow")
    st.info("Status: **Active** 🟢")
    st.divider()
    
    st.subheader("Automation Tasks")
    if st.button("🚀 Run System Diagnostics"):
        status = get_system_status()
        st.write(status)
    
    st.divider()
    st.caption("Developed by Sanjeev | v1.0")

# 4. Main Home Page UI
st.title("Welcome to Nexus Flow AI ⚡")

# Top Row Metrics (Automation Stats)
col1, col2, col3 = st.columns(3)
col1.metric("Tasks Automated", "12", "+2")
col2.metric("Response Time", "0.8s", "-0.1s")
col3.metric("System Health", "100%")

st.divider()

# 5. Chat Interface Logic
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am **Nexus Flow**. I can chat with you or execute automation tasks. How can I help?"}
    ]

# Display Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Enter command or chat..."):
    # User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Agent Response
    with st.chat_message("assistant"):
        model = initialize_agent()
        # Formatting history for Gemini
        history = [{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
        response = get_chat_response(model, prompt, history)
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    
