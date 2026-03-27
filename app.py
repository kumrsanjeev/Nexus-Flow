import streamlit as st
# Must be line 1
st.set_page_config(page_title="Nexus Flow Pro", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse

# UI Styling
st.markdown("<style>.stChatMessage { border-radius: 12px; border: 1px solid #30363d; }</style>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.title("Nexus Flow Pro 🤖")
    if st.button("🗑️ Clear Memory"):
        st.session_state.messages = []
        st.rerun()

# Display Chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Logic
if prompt := st.chat_input("Puchiye Sanjeev..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Nexus Flow is thinking...", expanded=False) as status:
            try:
                model = initialize_agent()
                # Correcting history for Gemini
                history = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
                
                full_res = get_chat_response(model, prompt, history)
                final_ans = ""

                # --- 1. IMAGE DISPLAY ---
                if "[GENERATE_IMAGE:" in full_res:
                    img_p = full_res.split("[GENERATE_IMAGE:")[1].split("]")[0].strip()
                    encoded_p = urllib.parse.quote(img_p)
                    img_url = f"https://image.pollinations.ai/prompt/{encoded_p}?width=1024&height=1024&model=flux&nologo=true"
                    
                    status.update(label="🎨 Image Created!", state="complete")
                    st.image(img_url, caption=f"Nexus Flow AI: {img_p}")
                    final_ans = f"Aapki image taiyar hai: **{img_p}**"

                # --- 2. THINKING DISPLAY ---
                elif "<thinking>" in full_res:
                    parts = full_res.split("</thinking>")
                    thinking_logic = parts[0].replace("<thinking>", "").strip()
                    st.write(thinking_logic) # Dropdown mein logic dikhega
                    final_ans = parts[1].strip()
                    status.update(label="Reasoning Complete", state="complete")
                
                else:
                    final_ans = full_res
                    status.update(label="Response Ready", state="complete")

            except Exception as e:
                final_ans = f"System Error: {e}"
                status.update(label="Error!", state="error")

        st.markdown(final_ans)
        st.session_state.messages.append({"role": "assistant", "content": final_ans})
        
