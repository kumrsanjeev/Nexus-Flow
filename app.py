import streamlit as st
from agent import initialize_agent, get_chat_response
import urllib.parse
import streamlit.components.v1 as components

# Page Setup
st.set_page_config(page_title="Nexus Flow AI", page_icon="⚡", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stChatMessage { border-radius: 12px; border: 1px solid #161B22; }
    </style>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("Nexus Flow 🤖")
    st.info("Status: Online 🟢")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.caption("Developed by Sanjeev")

# Chat History Session
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# User Input Logic
if prompt := st.chat_input("Kaise help karu Sanjeev?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Nexus Flow is working...", expanded=False) as status:
            try:
                # Initialize and Call AI
                model = initialize_agent()
                history = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
                
                full_res = get_chat_response(model, prompt, history)
                final_ans = ""

                # --- CASE 1: IMAGE GENERATION ---
                if "[GENERATE_IMAGE:" in full_res:
                    raw_prompt = full_res.split("[GENERATE_IMAGE:")[1].split("]")[0].strip()
                    clean_prompt = urllib.parse.quote(raw_prompt)
                    # High quality Flux model URL
                    img_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1024&height=1024&model=flux&nologo=true"
                    
                    st.image(img_url, caption=f"Generated: {raw_prompt}")
                    final_ans = f"✅ Image ready for: **{raw_prompt}**"
                    status.update(label="Image Generated!", state="complete")

                # --- CASE 2: THINKING LOGIC ---
                elif "<thinking>" in full_res:
                    parts = full_res.split("</thinking>")
                    thinking_content = parts[0].replace("<thinking>", "").strip()
                    st.write(thinking_content) # Dropdown mein dikhega
                    final_ans = parts[1].strip()
                    status.update(label="Thinking Complete!", state="complete")

                # --- CASE 3: DIRECT COMMANDS ---
                elif "open youtube" in prompt.lower():
                    js = '<script>window.open("https://youtube.com", "_blank");</script>'
                    components.html(js, height=0)
                    final_ans = "YouTube trigger kar diya hai! 📺"
                    status.update(label="Command Executed", state="complete")

                # --- CASE 4: NORMAL RESPONSE ---
                else:
                    final_ans = full_res
                    status.update(label="Done!", state="complete")

            except Exception as e:
                final_ans = f"Error: {e}"
                status.update(label="Failed!", state="error")

        # Display Final Answer and Save
        st.markdown(final_ans)
        st.session_state.messages.append({"role": "assistant", "content": final_ans})
        
