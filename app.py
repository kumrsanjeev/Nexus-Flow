import streamlit as st
st.set_page_config(page_title="Nexus Flow AI Pro", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse
import re

# 1. Session State (Improved Memory)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_history" not in st.session_state:
    st.session_state.api_history = []

# 2. Display History (With Image Persistence)
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m:
            st.image(m["image"])

# 3. User Input
if prompt := st.chat_input("Kaise help karu Sanjeev?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        final_ans = ""
        display_img = None
        
        with st.status("Nexus Flow is analyzing...", expanded=True) as status:
            try:
                model = initialize_agent()
                # Correct history sync
                full_res = get_chat_response(model, prompt, st.session_state.api_history)

                # IMAGE LOGIC
                if "[GENERATE_IMAGE:" in full_res:
                    raw_p = full_res.split("[GENERATE_IMAGE:")[1].split("]")[0].strip()
                    clean_p = urllib.parse.quote(raw_p)
                    display_img = f"https://image.pollinations.ai/prompt/{clean_p}?width=1024&height=1024&model=flux&nologo=true"
                    final_ans = f"✅ Image ready: **{raw_p}**"
                    status.update(label="🎨 Image Rendered!", state="complete")
                
                # THINKING LOGIC
                elif "<thinking>" in full_res:
                    parts = full_res.split("</thinking>")
                    thinking = parts[0].replace("<thinking>", "").strip()
                    st.expander("🧠 My Reasoning Process", expanded=False).write(thinking)
                    final_ans = parts[1].strip()
                    status.update(label="Logic Applied!", state="complete")
                
                else:
                    final_ans = full_res
                    status.update(label="Done!", state="complete")

            except Exception as e:
                final_ans = f"System Error: {e}"
                status.update(label="Failed!", state="error")

        # UI Rendering
        st.markdown(final_ans)
        if display_img:
            st.image(display_img)
        
        # 4. Save to Persistent State
        new_msg = {"role": "assistant", "content": final_ans}
        if display_img: new_msg["image"] = display_img
        
        st.session_state.messages.append(new_msg)
        st.session_state.api_history.append({"role": "user", "parts": [prompt]})
        st.session_state.api_history.append({"role": "model", "parts": [final_ans]})
        
