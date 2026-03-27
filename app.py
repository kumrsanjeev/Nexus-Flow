import streamlit as st
# Must be the first line
st.set_page_config(page_title="Nexus Flow AI", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse

# 1. Custom Styling
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; border: 1px solid #262730; }
    .stStatusWidget { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Sidebar
with st.sidebar:
    st.title("Nexus Flow 🤖")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.caption("Owner: Sanjeev")

# 4. Display History
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 5. User Input
if prompt := st.chat_input("Kaise help karu Sanjeev?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Nexus Flow is processing...", expanded=False) as status:
            try:
                model = initialize_agent()
                history = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
                
                full_res = get_chat_response(model, prompt, history)
                final_ans = ""

                # CASE 1: IMAGE GENERATION
                if "[GENERATE_IMAGE:" in full_res:
                    raw_p = full_res.split("[GENERATE_IMAGE:")[1].split("]")[0].strip()
                    # Safe URL encoding for spaces
                    clean_p = urllib.parse.quote(raw_p)
                    img_url = f"https://image.pollinations.ai/prompt/{clean_p}?width=1024&height=1024&model=flux&nologo=true"
                    
                    status.update(label="🎨 Image Created!", state="complete")
                    st.image(img_url, caption=f"Nexus Flow Generated: {raw_p}")
                    final_ans = f"✅ Image ready: **{raw_p}**. [Direct Link]({img_url})"

                # CASE 2: THINKING / EDIT MODE
                elif "<thinking>" in full_res:
                    parts = full_res.split("</thinking>")
                    thinking_process = parts[0].replace("<thinking>", "").strip()
                    st.info(f"🧠 Reasoning: {thinking_process}")
                    final_ans = parts[1].strip()
                    status.update(label="Thinking Complete!", state="complete")
                
                # CASE 3: NORMAL TEXT
                else:
                    final_ans = full_res
                    status.update(label="Done!", state="complete")

            except Exception as e:
                final_ans = f"Error: {e}"
                status.update(label="System Error!", state="error")

        st.markdown(final_ans)
        st.session_state.messages.append({"role": "assistant", "content": final_ans})
        
