import streamlit as st
from agent import initialize_agent, get_chat_response
import urllib.parse
import re

# Page Setup
st.set_page_config(page_title="Nexus Flow AI", page_icon="⚡", layout="wide")

# Session State for Gemini-like History
if "messages" not in st.session_state:
    st.session_state.messages = [] # Display history
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = [] # AI context memory

# --- SIDEBAR (New Chat & Controls) ---
with st.sidebar:
    st.title("Nexus Flow Pro 🤖")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_memory = []
        st.rerun()
    
    st.divider()
    if st.button("🗑️ Clear All History"):
        st.session_state.messages = []
        st.session_state.chat_memory = []
        st.rerun()
    st.caption(f"Owner: Sanjeev")

# --- MAIN CHAT INTERFACE ---
st.title("Nexus Flow AI ⚡")

# Display persistent history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m:
            st.image(m["image"])

# User Input
if prompt := st.chat_input("Kaise help karu Sanjeev?"):
    # Add User Message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Nexus Response Logic
    with st.chat_message("assistant"):
        with st.status("Nexus Flow is thinking...", expanded=False) as status:
            try:
                model = initialize_agent()
                full_res = get_chat_response(model, prompt, st.session_state.chat_memory)
                
                # Image Logic
                current_img_url = None
                if "[GENERATE_IMAGE:" in full_res:
                    img_prompt = full_res.split("[GENERATE_IMAGE:")[1].split("]")[0].strip()
                    encoded = urllib.parse.quote(img_prompt)
                    current_img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&model=flux&nologo=true"
                    full_res = f"✅ Image ready for: **{img_prompt}**"
                
                status.update(label="Response Ready!", state="complete")
                
            except Exception as e:
                if "429" in str(e):
                    full_res = "⚠️ Quota Limit Exceeded! Google ki free limit khatam ho gayi hai. Please 1-2 minute baad try karein."
                else:
                    full_res = f"Error: {e}"
                current_img_url = None
                status.update(label="Error!", state="error")

        # Final Display
        st.markdown(full_res)
        if current_img_url:
            st.image(current_img_url)

        # SAVE TO MEMORY (Like Gemini)
        msg_to_store = {"role": "assistant", "content": full_res}
        if current_img_url:
            msg_to_store["image"] = current_img_url
        
        st.session_state.messages.append(msg_to_store)
        
        # Save to AI Memory (Context)
        st.session_state.chat_memory.append({"role": "user", "parts": [prompt]})
        st.session_state.chat_memory.append({"role": "model", "parts": [full_res]})
        
