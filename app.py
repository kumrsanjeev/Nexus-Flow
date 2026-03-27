import streamlit as st
# CRITICAL: Page config must be first
st.set_page_config(page_title="Nexus Flow Pro", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse
import re

# Persistent Chat State
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
    st.divider()
    st.caption("Owner: Sanjeev")

# Display Messages (Crash-Proof Loop)
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        # Using .get() prevents "AttributeError" if image is missing
        if m.get("image"):
            st.image(m["image"])

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
                    full_res = get_chat_response(model, prompt, st.session_state.chat_memory)
                    
                    # Parsing Reasoning and Images
                    if "<thinking>" in full_res:
                        full_res = full_res.split("</thinking>")[-1].strip()

                    if "[GENERATE_IMAGE:" in full_res:
                        match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', full_res)
                        if match:
                            img_p = match.group(1).strip()
                            img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(img_p)}?width=1024&height=1024&model=flux"
                            final_ans = f"✅ Image ready: **{img_p}**"
                    
                    if not final_ans: final_ans = full_res
                    status.update(label="Done!", state="complete")
                else:
                    final_ans = "System Initialization Failed. Check Secrets."
                    status.update(label="Error!", state="error")

            except Exception as e:
                final_ans = f"API Error: {e}"
                status.update(label="Failed!", state="error")

        # UI Rendering
        st.markdown(final_ans)
        if img_url: st.image(img_url)

        # Save to Memory
        st.session_state.messages.append({"role": "assistant", "content": final_ans, "image": img_url})
        st.session_state.chat_memory.append({"role": "user", "parts": [prompt]})
        st.session_state.chat_memory.append({"role": "model", "parts": [final_ans]})
        
