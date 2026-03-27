import streamlit as st
# MUST BE LINE 1
st.set_page_config(page_title="Nexus Flow | Pro", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse
import re

# Persistent Memory State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_history" not in st.session_state:
    st.session_state.api_history = []

# Sidebar
with st.sidebar:
    st.title("Nexus Flow Pro 🤖")
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.api_history = []
        st.rerun()
    st.divider()
    st.caption("Owner: Sanjeev")

# Display History
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m and m["image"]:
            st.image(m["image"])

# User Input
if prompt := st.chat_input("Puchiye Sanjeev..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Variables initialized to avoid NameError
        final_ans = ""
        img_url = None
        
        with st.status("Nexus Flow is thinking...", expanded=False) as status:
            try:
                model = initialize_agent()
                full_res = get_chat_response(model, prompt, st.session_state.api_history)
                
                # Handling Thinking logic
                if "<thinking>" in full_res:
                    parts = full_res.split("</thinking>")
                    st.info(f"🧠 Reasoning: {parts[0].replace('<thinking>', '').strip()}")
                    full_res = parts[1].strip() if len(parts) > 1 else full_res

                # Handling Image Generation
                if "[GENERATE_IMAGE:" in full_res:
                    img_match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', full_res)
                    if img_match:
                        img_p = img_match.group(1).strip()
                        encoded_p = urllib.parse.quote(img_p)
                        img_url = f"https://image.pollinations.ai/prompt/{encoded_p}?width=1024&height=1024&model=flux&nologo=true"
                        final_ans = f"✅ Image ready for: **{img_p}**"
                
                if not final_ans:
                    final_ans = full_res

                status.update(label="Done!", state="complete")
                
            except Exception as e:
                final_ans = f"System Error: {e}"
                status.update(label="Failed!", state="error")

        # UI Output
        st.markdown(final_ans)
        if img_url:
            st.image(img_url)

        # Save to Memory
        msg_store = {"role": "assistant", "content": final_ans, "image": img_url}
        st.session_state.messages.append(msg_store)
        st.session_state.api_history.append({"role": "user", "parts": [prompt]})
        st.session_state.api_history.append({"role": "model", "parts": [final_ans]})
        
