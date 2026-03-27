import streamlit as st
# CRITICAL: Page config must be first line
st.set_page_config(page_title="Nexus Flow Pro", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse
import re

# Memory Persistence
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_history" not in st.session_state:
    st.session_state.api_history = []

with st.sidebar:
    st.title("Nexus Flow Pro 🤖")
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.api_history = []
        st.rerun()
    st.divider()
    st.caption("Owner: Sanjeev")

# Display Persistent History
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("image"): st.image(m["image"])

# Input Logic
if prompt := st.chat_input("Puchiye Sanjeev..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        final_ans = ""
        img_url = None
        
        with st.status("Nexus Flow is thinking...", expanded=False) as status:
            try:
                model = initialize_agent()
                if model:
                    full_res = get_chat_response(model, prompt, st.session_state.api_history)
                    
                    # 1. Parse Reasoning
                    if "<thinking>" in full_res:
                        parts = full_res.split("</thinking>")
                        st.info(f"🧠 Logic: {parts[0].replace('<thinking>', '').strip()}")
                        full_res = parts[1].strip() if len(parts) > 1 else full_res

                    # 2. Parse Image
                    if "[GENERATE_IMAGE:" in full_res:
                        match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', full_res)
                        if match:
                            img_p = match.group(1).strip()
                            img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(img_p)}?width=1024&height=1024&model=flux"
                            final_ans = f"✅ Image ready: **{img_p}**"
                    
                    if not final_ans: final_ans = full_res

                    status.update(label="Done!", state="complete")
                    st.markdown(final_ans)
                    if img_url: st.image(img_url)
                    
                    # 3. Save to History
                    st.session_state.messages.append({"role": "assistant", "content": final_ans, "image": img_url})
                    st.session_state.api_history.append({"role": "user", "parts": [prompt]})
                    st.session_state.api_history.append({"role": "model", "parts": [final_ans]})
                else:
                    status.update(label="System Error!", state="error")
                    st.error("Model scanner fail ho gaya. Ek baar naya API Key try karein.")
            except Exception as e:
                status.update(label="Failed!", state="error")
                st.error(f"Error: {e}")
                
