import streamlit as st
# Must be the first line
st.set_page_config(page_title="Nexus Flow Pro", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response

# Memory Setup
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = []

with st.sidebar:
    st.title("Nexus Flow Pro 🤖")
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.chat_memory = []
        st.rerun()
    st.caption("Owner: Sanjeev")

# Display Messages
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# User Input
if prompt := st.chat_input("Puchiye Sanjeev..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Nexus Flow is thinking...", expanded=False):
            model = initialize_agent()
            # Calling the fix with chat_memory
            res = get_chat_response(model, prompt, st.session_state.chat_memory)
        
        st.markdown(res)
        
        # Update UI & API Memory
        st.session_state.messages.append({"role": "assistant", "content": res})
        st.session_state.chat_memory.append({"role": "user", "parts": [prompt]})
        st.session_state.chat_memory.append({"role": "model", "parts": [res]})
        
