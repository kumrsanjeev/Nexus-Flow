import streamlit as st
# CRITICAL: This MUST be the very first line
st.set_page_config(page_title="Nexus Flow AI", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse

# 1. Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. Sidebar
with st.sidebar:
    st.title("Nexus Flow 🤖")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    st.caption("Owner: Sanjeev")

# 3. Display Messages
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 4. Input Logic
if prompt := st.chat_input("Kaise help karu Sanjeev?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Nexus Flow is working...", expanded=False) as status:
            try:
                model = initialize_agent()
                history = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
                
                full_res = get_chat_response(model, prompt, history)
                final_ans = ""

                # CASE 1: IMAGE
                if "[GENERATE_IMAGE:" in full_res:
                    raw_p = full_res.split("[GENERATE_IMAGE:")[1].split("]")[0].strip()
                    clean_p = urllib.parse.quote(raw_p)
                    img_url = f"https://image.pollinations.ai/prompt/{clean_p}?width=1024&height=1024&model=flux"
                    st.image(img_url, caption=f"Generated: {raw_p}")
                    final_ans = f"✅ Image ready for: **{raw_p}**"
                    status.update(label="Image Done!", state="complete")

                # CASE 2: THINKING
                elif "<thinking>" in full_res:
                    parts = full_res.split("</thinking>")
                    st.write(parts[0].replace("<thinking>", "").strip())
                    final_ans = parts[1].strip()
                    status.update(label="Reasoning Complete!", state="complete")
                
                # CASE 3: NORMAL
                else:
                    final_ans = full_res
                    status.update(label="Done!", state="complete")

            except Exception as e:
                final_ans = f"Error: {e}"
                status.update(label="System Error!", state="error")

        st.markdown(final_ans)
        st.session_state.messages.append({"role": "assistant", "content": final_ans})
