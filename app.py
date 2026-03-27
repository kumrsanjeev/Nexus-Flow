import streamlit as st
from agent import initialize_agent, get_chat_response
import urllib.parse
import re

# Page Setup
st.set_page_config(page_title="Nexus Flow AI", page_icon="⚡", layout="wide")

# Persistent History like Gemini
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("Nexus Flow Pro 🤖")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_memory = []
        st.rerun()
    
    st.divider()
    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.session_state.chat_memory = []
        st.rerun()
    st.caption(f"Owner: Sanjeev")

# --- MAIN UI ---
st.title("Nexus Flow AI ⚡")

# Display History
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m:
            st.image(m["image"])

# User Input
if prompt := st.chat_input("Kaise help karu Sanjeev?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Nexus Flow is thinking...", expanded=False) as status:
            try:
                model = initialize_agent()
                if model:
                    full_res = get_chat_response(model, prompt, st.session_state.chat_memory)
                    
                    # Logic for Image & Thinking
                    current_img = None
                    if "[GENERATE_IMAGE:" in full_res:
                        img_p = full_res.split("[GENERATE_IMAGE:")[1].split("]")[0].strip()
                        encoded = urllib.parse.quote(img_p)
                        current_img = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&model=flux&nologo=true"
                        full_res = f"✅ Image ready for: **{img_p}**"
                    
                    status.update(label="Response Ready!", state="complete")
                    
                    # Display Result
                    st.markdown(full_res)
                    if current_img:
                        st.image(current_img)
                    
                    # Update Memory
                    msg_store = {"role": "assistant", "content": full_res}
                    if current_img: msg_store["image"] = current_img
                    st.session_state.messages.append(msg_store)
                    
                    st.session_state.chat_memory.append({"role": "user", "parts": [prompt]})
                    st.session_state.chat_memory.append({"role": "model", "parts": [full_res]})
                else:
                    st.error("Model could not be loaded. Check API Key/Quota.")

            except Exception as e:
                status.update(label="Failed!", state="error")
                if "429" in str(e):
                    st.warning("Quota Full! Please wait 60 seconds.")
                else:
                    st.error(f"Error: {e}")
                    
