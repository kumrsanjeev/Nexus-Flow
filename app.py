import streamlit as st
# Critical: Page config must be first
st.set_page_config(page_title="Nexus Flow Pro", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse

# Sidebar
with st.sidebar:
    st.title("Nexus Flow Pro 🤖")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Messages
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# User Input
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
                final_output = ""

                # --- DIRECT IMAGE GENERATION ---
                if "[GENERATE_IMAGE:" in full_res:
                    img_prompt = full_res.split("[GENERATE_IMAGE:")[1].split("]")[0].strip()
                    encoded_p = urllib.parse.quote(img_prompt)
                    img_url = f"https://image.pollinations.ai/prompt/{encoded_p}?width=1024&height=1024&model=flux&nologo=true"
                    
                    status.update(label="🎨 Image Generated!", state="complete")
                    # Direct Display like Gemini
                    st.image(img_url, caption=f"Nexus Flow Created: {img_prompt}", use_container_width=True)
                    final_output = f"Maine aapke liye **{img_prompt}** bana di hai. [Direct Link]({img_url})"

                # --- DEEP THINKING (ChatGPT style) ---
                elif "<thinking>" in full_res:
                    parts = full_res.split("</thinking>")
                    thinking_txt = parts[0].replace("<thinking>", "").strip()
                    st.write(thinking_txt) # Shows AI logic in the dropdown
                    final_output = parts[1].strip()
                    status.update(label="Thinking complete!", state="complete")
                
                else:
                    final_output = full_res
                    status.update(label="Done!", state="complete")

            except Exception as e:
                final_output = f"System Error: {e}. Check API Key."
                status.update(label="Failed!", state="error")

        st.markdown(final_output)
        st.session_state.messages.append({"role": "assistant", "content": final_output})
        
