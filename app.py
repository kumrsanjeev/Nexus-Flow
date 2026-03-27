import streamlit as st
# CRITICAL: Page config must be the very first line
st.set_page_config(page_title="Nexus Flow | Context Pro", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse
import re

# Persistent States
if "messages" not in st.session_state:
    st.session_state.messages = [] # For UI
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = [] # For API Memory

# --- SIDEBAR ---
with st.sidebar:
    st.title("Nexus Flow Pro 🤖")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_memory = []
        st.rerun()
    st.divider()
    if st.button("🗑️ Clear Context"):
        st.session_state.messages = []
        st.session_state.chat_memory = []
        st.rerun()
    st.caption("Owner: Sanjeev | Context v1.0")

# --- CHAT DISPLAY ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m: st.image(m["image"])

# --- INPUT LOGIC ---
if prompt := st.chat_input("Puchiye Sanjeev..."):
    # Add to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Nexus Flow is thinking deeply...", expanded=False) as status:
            try:
                model = initialize_agent()
                # Get Response with Memory Context
                full_res = get_chat_response(model, prompt, st.session_state.chat_memory)
                
                final_ans = ""
                img_url = None

                # 1. Parse Image
                if "[GENERATE_IMAGE:" in full_res:
                    match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', full_res)
                    if match:
                        p = match.group(1).strip()
                        img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?width=1024&height=1024&model=flux"
                        final_ans = f"✅ Image ready: **{p}**"
                
                if not final_ans: final_ans = full_res
                status.update(label="Response Ready!", state="complete")

            except Exception as e:
                final_ans = f"Error: {e}"
                status.update(label="System Error!", state="error")

        # UI Rendering
        st.markdown(final_ans)
        if img_url: st.image(img_url)

        # 2. SAVE TO PERSISTENT MEMORY (CRITICAL)
        msg_store = {"role": "assistant", "content": final_ans}
        if img_url: msg_store["image"] = img_url
        st.session_state.messages.append(msg_store)
        
        # Save to API History (Correct Format)
        st.session_state.chat_memory.append({"role": "user", "parts": [prompt]})
        st.session_state.chat_memory.append({"role": "model", "parts": [final_ans]})
        
