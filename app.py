import streamlit as st
st.set_page_config(page_title="Nexus Flow Pro", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse
import re

if "messages" not in st.session_state: st.session_state.messages = []
if "memory" not in st.session_state: st.session_state.memory = []

# Input
if prompt := st.chat_input("Puchiye Sanjeev..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    model = initialize_agent()
    response_text = get_chat_response(model, prompt, st.session_state.memory)
    
    img_url = None
    if "[GENERATE_IMAGE:" in response_text:
        match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', response_text)
        if match:
            p = match.group(1).strip()
            # Direct Image URL from Pollinations (Free & Fast)
            img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?width=1024&height=1024&nologo=true"
            response_text = f"🎨 Generating image for: **{p}**"

    st.session_state.messages.append({"role": "assistant", "content": response_text, "image": img_url})
    st.session_state.memory.append({"role": "user", "parts": [prompt]})
    st.session_state.memory.append({"role": "model", "parts": [response_text]})
    st.rerun()

# Display
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("image"): st.image(m["image"])
            
