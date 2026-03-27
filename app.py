import streamlit as st
# CRITICAL: Page config must be line 1
st.set_page_config(page_title="Nexus Flow Pro", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse
import re

# Persistent memory
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = []

# Sidebar
with st.sidebar:
    st.title("Nexus Flow Pro 🤖")
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.chat_memory = []
        st.rerun()
    st.divider()
    st.caption("Owner: Sanjeev")

# Display
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m: st.image(m["image"])

# Input
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
                    
                    # Image parsing
                    img_url = None
                    if "[GENERATE_IMAGE:" in full_res:
                        p_match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', full_res)
                        if p_match:
                            clean_p = urllib.parse.quote(p_match.group(1))
                            img_url = f"https://image.pollinations.ai/prompt/{clean_p}?width=1024&height=1024&model=flux&nologo=true"
                            full_res = f"✅ Image ready for: **{p_match.group(1)}**"
                    
                    # Thinking parsing
                    if "<thinking>" in full_res:
                        full_res = full_res.split("</thinking>")[-1].strip()

                    status.update(label="Done!", state="complete")
                    st.markdown(full_res)
                    if img_url: st.image(img_url)
                    
                    # Save history
                    msg_store = {"role": "assistant", "content": full_res}
                    if img_url: msg_store["image"] = img_url
                    st.session_state.messages.append(msg_store)
                    st.session_state.chat_memory.append({"role": "user", "parts": [prompt]})
                    st.session_state.chat_memory.append({"role": "model", "parts": [full_res]})
                else:
                    status.update(label="Initialization Failed!", state="error")
                    st.error("Sanjeev, saare models fail ho gaye. Ek baar API Key check karo.")
            except Exception as e:
                status.update(label="Error!", state="error")
                st.error(f"System Error: {e}")
                
