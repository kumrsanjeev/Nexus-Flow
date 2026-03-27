import streamlit as st
st.set_page_config(page_title="Nexus Flow AI", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse
import re

# Persistent Chat State
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

# Display History (Persistent)
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
                full_res = get_chat_response(model, prompt, st.session_state.api_history)
                
                # Handling logic
                if "<thinking>" in full_res:
                    full_res = full_res.split("</thinking>")[-1].strip()

                if "[GENERATE_IMAGE:" in full_res:
                    match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', full_res)
                    if match:
                        img_p = match.group(1).strip()
                        img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(img_p)}?width=1024&height=1024&model=flux"
                        final_ans = f"✅ Image ready for: **{img_p}**"
                
                if not final_ans: final_ans = full_res
                status.update(label="Done!", state="complete")
                
            except Exception as e:
                status.update(label="Failed!", state="error")
                if "429" in str(e): final_ans = "⚠️ Quota full! Please wait 60 seconds."
                else: final_ans = f"Error: {e}"

        # Display Final Result
        st.markdown(final_ans)
        if img_url: st.image(img_url)
        
        # Save to Memory (Crucial)
        st.session_state.messages.append({"role": "assistant", "content": final_ans, "image": img_url})
        st.session_state.api_history.append({"role": "user", "parts": [prompt]})
        st.session_state.api_history.append({"role": "model", "parts": [final_ans]})
        
