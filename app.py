import streamlit as st
# Critical: Page config must be first
st.set_page_config(page_title="Nexus Flow Pro", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse

# Custom Sidebar
with st.sidebar:
    st.title("Nexus Flow Pro 🤖")
    st.info("Status: Active 🟢")
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.chat_memory = []
        st.rerun()
    st.divider()
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.chat_memory = []
        st.rerun()
    st.caption("Owner: Sanjeev")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = []

# Display Messages
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m:
            st.image(m["image"])

# User Input
if prompt := st.chat_input("Kaise help karu Sanjeev?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # ChatGPT-style "Thinking" Status
        with st.status("Nexus Flow is thinking...", expanded=False) as status:
            try:
                model = initialize_agent()
                # Properly format history for Gemini API
                full_res = get_chat_response(model, prompt, st.session_state.chat_memory)
                final_output = ""

                # --- CASE 1: DIRECT IMAGE GENERATION ---
                if "[GENERATE_IMAGE:" in full_res:
                    img_prompt = full_res.split("[GENERATE_IMAGE:")[1].split("]")[0].strip()
                    encoded_p = urllib.parse.quote(img_prompt)
                    # High quality Flux model URL
                    img_url = f"https://image.pollinations.ai/prompt/{encoded_p}?width=1024&height=1024&model=flux&nologo=true"
                    
                    status.update(label="🎨 Image Generated!", state="complete")
                    # Direct Display like Gemini
                    st.image(img_url, caption=f"Nexus Flow Created: {img_prompt}", use_container_width=True)
                    final_output = f"Maine aapke liye **{img_prompt}** generate kar di hai."
                    current_img = img_url

                # --- CASE 2: DEEP THINKING (ChatGPT style) ---
                elif "<thinking>" in full_res:
                    parts = full_res.split("</thinking>")
                    thinking_txt = parts[0].replace("<thinking>", "").strip()
                    st.write(thinking_txt) # Shows AI logic inside the dropdown
                    final_output = parts[1].strip()
                    status.update(label="Thinking complete!", state="complete")
                    current_img = None
                
                else:
                    final_output = full_res
                    status.update(label="Done!", state="complete")
                    current_img = None

            except Exception as e:
                if "429" in str(e):
                    final_output = "⚠️ Quota Limit Exceeded! Google ki free limit khatam ho gayi hai. Please 1-2 minute baad try karein."
                else:
                    final_output = f"System Error: {e}. Check API Key."
                status.update(label="Failed!", state="error")
                current_img = None

        # Final Chat Response (outside status box)
        st.markdown(final_output)
        
        # Save to memory (Display + Context)
        msg_to_store = {"role": "assistant", "content": final_output}
        if current_img:
            msg_to_store["image"] = current_img
        st.session_state.messages.append(msg_to_store)
        
        st.session_state.chat_memory.append({"role": "user", "parts": [prompt]})
        st.session_state.chat_memory.append({"role": "model", "parts": [final_output]})
        
