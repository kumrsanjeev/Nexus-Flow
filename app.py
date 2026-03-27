import streamlit as st
# Must be first
st.set_page_config(page_title="Nexus Flow Pro", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse
import re

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

# Display history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m: st.image(m["image"])

if prompt := st.chat_input("Puchiye Sanjeev..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Nexus Flow is thinking...", expanded=False) as status:
            try:
                model = initialize_agent()
                full_res = get_chat_response(model, prompt, st.session_state.chat_memory)
                
                final_output = ""
                img_url = None

                # Image parsing
                if "[GENERATE_IMAGE:" in full_res:
                    p_match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', full_res)
                    if p_match:
                        clean_p = urllib.parse.quote(p_match.group(1))
                        img_url = f"https://image.pollinations.ai/prompt/{clean_p}?width=1024&height=1024&model=flux&nologo=true"
                        final_output = f"✅ Image ready: **{p_match.group(1)}**"
                
                # Thinking removal
                if not final_output:
                    final_output = full_res.split("</thinking>")[-1].strip()

                status.update(label="Done!", state="complete")
                st.markdown(final_output)
                if img_url: st.image(img_url)
                
                # Save to History
                msg_store = {"role": "assistant", "content": final_output}
                if img_url: msg_store["image"] = img_url
                st.session_state.messages.append(msg_store)
                st.session_state.chat_memory.append({"role": "user", "parts": [prompt]})
                st.session_state.chat_memory.append({"role": "model", "parts": [final_output]})
                
            except Exception as e:
                status.update(label="Failed!", state="error")
                st.error(f"Error: {e}")
                
