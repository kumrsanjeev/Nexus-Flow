import streamlit as st
from agent import initialize_agent, get_chat_response
from tools import get_system_status

# Page Config
st.set_page_config(page_title="Nexus Flow AI", page_icon="⚡", layout="wide")

# Custom Dark Theme CSS
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stChatMessage { border-radius: 12px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("Nexus Flow 🤖")
    st.info("Status: Active 🟢")
    if st.button("🚀 Run Diagnostics"):
        st.success(get_system_status())
    st.divider()
    st.caption("Owner: Sanjeev")

st.title("Nexus Flow AI ⚡")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Kaise help karu Sanjeev?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Bot Response Logic
    with st.chat_message("assistant"):
        # Shortcut for "Open Youtube"
        if "open youtube" in prompt.lower():
            res = "Opening YouTube for you: [Click here to open YouTube](https://youtube.com)"
            st.markdown(res)
        else:
            try:
                model = initialize_agent()
                # Converting Streamlit roles to Gemini roles
                formatted_history = []
                for m in st.session_state.messages[:-1]:
                    role = "model" if m["role"] == "assistant" else "user"
                    formatted_history.append({"role": role, "parts": [m["content"]]})
                
                res = get_chat_response(model, prompt, formatted_history)
                st.markdown(res)
            except Exception as e:
                res = f"Error: {e}. Check if Gemini API is enabled."
                st.error(res)
        
        st.session_state.messages.append({"role": "assistant", "content": res})
        
