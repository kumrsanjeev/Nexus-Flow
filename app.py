import streamlit as st
st.set_page_config(page_title="Nexus Flow Pro", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse
import re

if "messages" not in st.session_state: st.session_state.messages = []
if "api_history" not in st.session_state: st.session_state.api_history = []

# Sidebar
with st.sidebar:
    st.title("Nexus Flow Pro 🤖")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.api_history = []
        st.rerun()

# 3. Display Messages (FIXED Line 19)
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        # FIX: Use .get() to prevent AttributeError
        img_data = m.get("image")
        if img_data:
            st.image(img_data)

# 4. Input Logic
if prompt := st.chat_input("Kaise help karu Sanjeev?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        final_ans = ""
        display_img = None
        
        with st.status("Analyzing...", expanded=False) as status:
            try:
                model = initialize_agent()
                full_res = get_chat_response(model, prompt, st.session_state.api_history)
                
                # Logic: Image Parsing
                if "[GENERATE_IMAGE:" in full_res:
                    raw_p = full_res.split("[GENERATE_IMAGE:")[1].split("]")[0].strip()
                    display_img = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(raw_p)}?width=1024&height=1024&nologo=true"
                    final_ans = f"✅ Image created: **{raw_p}**"
                
                # Logic: Thinking Parsing
                elif "<thinking>" in full_res:
                    parts = full_res.split("</thinking>")
                    st.expander("🧠 Reasoning").write(parts[0].replace("<thinking>", "").strip())
                    final_ans = parts[1].strip()
                else:
                    final_ans = full_res
                
                status.update(label="Done!", state="complete")
            except Exception as e:
                final_ans = f"System Error: {e}"
                status.update(label="Failed!", state="error")

        st.markdown(final_ans)
        if display_img: st.image(display_img)
        
        # Save to session (persistent)
        st.session_state.messages.append({"role": "assistant", "content": final_ans, "image": display_img})
        st.session_state.api_history.append({"role": "user", "parts": [prompt]})
        st.session_state.api_history.append({"role": "model", "parts": [final_ans]})
        
