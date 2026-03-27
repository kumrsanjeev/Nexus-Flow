import streamlit as st
# Line 1 must be page config
st.set_page_config(page_title="Nexus Flow Pro", layout="wide")

from agent import initialize_agent, get_chat_response

if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_history" not in st.session_state:
    st.session_state.api_history = []

# Sidebar and UI Logic... (Aapka purana code)

if prompt := st.chat_input("Puchiye Sanjeev..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        model = initialize_agent()
        # FIX: Memory is passed correctly here
        res = get_chat_response(model, prompt, st.session_state.api_history)
        st.markdown(res)
        
        # Save to Memory
        st.session_state.messages.append({"role": "assistant", "content": res})
        st.session_state.api_history.append({"role": "user", "parts": [prompt]})
        st.session_state.api_history.append({"role": "model", "parts": [res]})
        
