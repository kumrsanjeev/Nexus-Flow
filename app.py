import streamlit as st
st.set_page_config(page_title="Nexus Flow Pro (OpenAI)", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse
import re

# Session State for History
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("Nexus Flow Pro 🤖")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    st.caption("Powered by OpenAI")

# Display Messages (Crash-Proof)
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("image"):
            st.image(m["image"])

# Input Logic
if prompt := st.chat_input("Kaise help karu Sanjeev?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        final_ans = ""
        display_img = None
        
        with st.status("GPT-4o is thinking...", expanded=False) as status:
            client = initialize_agent()
            if client:
                # Prepare history for OpenAI format
                history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
                
                full_res = get_chat_response(client, prompt, history)

                # Image Parsing
                if "[GENERATE_IMAGE:" in full_res:
                    raw_p = full_res.split("[GENERATE_IMAGE:")[1].split("]")[0].strip()
                    display_img = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(raw_p)}?width=1024&height=1024&nologo=true"
                    final_ans = f"✅ Image ready: **{raw_p}**"
                
                # Thinking Parsing
                elif "<thinking>" in full_res:
                    parts = full_res.split("</thinking>")
                    st.expander("🧠 Reasoning").write(parts[0].replace("<thinking>", "").strip())
                    final_ans = parts[1].strip()
                else:
                    final_ans = full_res
                
                status.update(label="Done!", state="complete")

        st.markdown(final_ans)
        if display_img: st.image(display_img)
        
        st.session_state.messages.append({"role": "assistant", "content": final_ans, "image": display_img})
        
