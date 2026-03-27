import streamlit as st
st.set_page_config(page_title="Nexus Flow Pro")

from agent import initialize_agent, get_chat_response

if "messages" not in st.session_state: st.session_state.messages = []
if "memory" not in st.session_state: st.session_state.memory = []

# Input
if prompt := st.chat_input("Puchiye Sanjeev..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant"):
        model = initialize_agent()
        if model:
            # FIX: Memory pass karne ka sahi tarika
            res = get_chat_response(model, prompt, st.session_state.memory)
            st.write(res)
            st.session_state.messages.append({"role": "assistant", "content": res})
            
            # API Memory Update
            st.session_state.memory.append({"role": "user", "parts": [prompt]})
            st.session_state.memory.append({"role": "model", "parts": [res]})
        else:
            st.error("API Key check karein!")
            
