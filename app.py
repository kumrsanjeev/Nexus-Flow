import streamlit as st
from agent import initialize_agent, get_chat_response
import urllib.parse
import re

# MUST BE FIRST
st.set_page_config(page_title="Nexus Flow AI", page_icon="⚡", layout="wide")

# Persistent Memory Setup
if "messages" not in st.session_state:
    st.session_state.messages = [] # For Display
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = [] # For AI Context

# Sidebar
with st.sidebar:
    st.title("Nexus Flow Pro 🤖")
    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.session_state.chat_memory = []
        st.rerun()
    st.divider()
    st.caption("Owner: Sanjeev")

# Header
st.title("Nexus Flow AI ⚡")

# Display Persistent History (Like Gemini)
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m:
            st.image(m["image"])

# Input Logic
if prompt := st.chat_input("Puchiye Sanjeev..."):
    # 1. Show User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Nexus Response
    with st.chat_message("assistant"):
        with st.status("Nexus Flow is thinking...", expanded=False) as status:
            try:
                model = initialize_agent()
                # Get Response with Memory
                full_res = get_chat_response(model, prompt, st.session_state.chat_memory)
                
                # Image Check
                img_url = None
                if "[GENERATE_IMAGE:" in full_res:
                    img_prompt = full_res.split("[GENERATE_IMAGE:")[1].split("]")[0].strip()
                    encoded = urllib.parse.quote(img_prompt)
                    img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&model=flux&nologo=true"
                    full_res = f"✅ Image ready: **{img_prompt}**"
                
                status.update(label="Done!", state="complete")
            except Exception as e:
                full_res = f"Error: {e}"
                status.update(label="Failed!", state="error")

        # Display Final
        st.markdown(full_res)
        if img_url:
            st.image(img_url)

        # 3. SAVE TO MEMORY (CRITICAL)
        # Update Display History
        msg_store = {"role": "assistant", "content": full_res}
        if img_url: msg_store["image"] = img_url
        st.session_state.messages.append(msg_store)
        
        # Update AI Context History
        st.session_state.chat_memory.append({"role": "user", "parts": [prompt]})
        st.session_state.chat_memory.append({"role": "model", "parts": [full_res]})
        
