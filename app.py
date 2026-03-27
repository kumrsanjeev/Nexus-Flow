import streamlit as st
# CRITICAL: This MUST be the first Streamlit command
st.set_page_config(page_title="Nexus Flow AI", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse
import streamlit.components.v1 as components

# 1. Sidebar & Reset
with st.sidebar:
    st.title("Nexus Flow 🤖")
    st.info("Status: Online 🟢")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.caption("Owner: Sanjeev | v2.1")

# 2. Session State for Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Main Dashboard UI
st.title("Nexus Flow AI 🚀")

# Display Messages
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 4. Input Logic
if prompt := st.chat_input("Kaise help karu Sanjeev?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Nexus Flow is thinking...", expanded=False) as status:
            try:
                model = initialize_agent()
                history = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
                
                full_res = get_chat_response(model, prompt, history)
                final_ans = ""

                # --- IMAGE GENERATION ---
                if "[GENERATE_IMAGE:" in full_res:
                    raw_p = full_res.split("[GENERATE_IMAGE:")[1].split("]")[0].strip()
                    clean_p = urllib.parse.quote(raw_p)
                    # Updated high-quality image URL
                    img_url = f"https://image.pollinations.ai/prompt/{clean_p}?width=1024&height=1024&model=flux"
                    
                    st.image(img_url, caption=f"Nexus Flow Generated: {raw_p}")
                    final_ans = f"✅ Image ready: **{raw_p}**"
                    status.update(label="Image Generated!", state="complete")

                # --- THINKING LOGIC ---
                elif "<thinking>" in full_res:
                    parts = full_res.split("</thinking>")
                    thinking_txt = parts[0].replace("<thinking>", "").strip()
                    st.write(thinking_txt) # Shows in status dropdown
                    final_ans = parts[1].strip()
                    status.update(label="Reasoning Complete!", state="complete")

                # --- NORMAL RESPONSE ---
                else:
                    final_ans = full_res
                    status.update(label="Done!", state="complete")

            except Exception as e:
                final_ans = f"Error: {e}"
                status.update(label="System Error!", state="error")

        # Final Markdown Display
        st.markdown(final_ans)
        st.session_state.messages.append({"role": "assistant", "content": final_ans})
        
