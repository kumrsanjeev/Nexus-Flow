import streamlit as st
from agent import initialize_agent, get_chat_response
from tools import get_system_status

st.set_page_config(page_title="Nexus Flow AI", page_icon="🤖")

st.title("Nexus Flow AI 🚀")
st.caption("Chatbot + Automation Agent powered by Gemini")

# Initialize Gemini Model
model = initialize_agent()

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for Automation Tools
with st.sidebar:
    st.header("Automation Tools")
    if st.button("Check System Status"):
        status = get_system_status()
        st.success(status)

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("How can I help you today?"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        # We pass history excluding the last message to get_chat_response
        history = [{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
        full_response = get_chat_response(model, prompt, history)
        st.markdown(full_response)
    
    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
  
