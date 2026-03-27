import streamlit as st
from agent import initialize_agent, get_chat_response
from tools import get_system_status
import streamlit.components.v1 as components

# 1. Page Configuration
st.set_page_config(page_title="Nexus Flow AI", page_icon="⚡", layout="wide")

# 2. Custom CSS for Dark Theme & Chat Bubbles
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stChatMessage { border-radius: 15px; border: 1px solid #161B22; padding: 10px; }
    .stStatusWidget { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Sidebar Branding
with st.sidebar:
    st.image("https://img.icons8.com/nolan/512/artificial-intelligence.png", width=80)
    st.title("Nexus Flow")
    st.info("Status: Online 🟢")
    if st.button("🚀 Run Diagnostics"):
        st.write(get_system_status())
    st.divider()
    st.caption("Developed by Sanjeev | v2.0")

st.title("Nexus Flow AI ⚡")

# 4. Session State for Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. User Input & Agent Logic
if prompt := st.chat_input("Kaise help karu Sanjeev?"):
    # Show User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Response Generation
    with st.chat_message("assistant"):
        with st.status("Nexus Flow is processing...", expanded=False) as status:
            try:
                # Initialize Brain
                model = initialize_agent()
                
                # Format History for Gemini (User -> Model)
                formatted_history = []
                for m in st.session_state.messages[:-1]:
                    role = "model" if m["role"] == "assistant" else "user"
                    formatted_history.append({"role": role, "parts": [m["content"]]})
                
                # Get Response from AI
                full_res = get_chat_response(model, prompt, formatted_history)
                final_display_text = ""

                # --- IMAGE GENERATION LOGIC ---
if "[GENERATE_IMAGE:" in full_res:
    img_prompt = full_res.split("[GENERATE_IMAGE:")[1].split("]")[0].strip()
    status.update(label="Generating Image... 🎨", state="running")
    
    # URL ko encode karna zaroori hai (Spaces ko %20 se replace karein)
    encoded_prompt = img_prompt.replace(" ", "%20")
    
    # Direct reliable URL with flux model
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux&nologo=true"
    
    # Displaying the image properly
    st.image(image_url, caption=f"Nexus Flow Generated: {img_prompt}", use_container_width=True)
    
    # Optional: Download button add karna
    st.markdown(f"[📥 Download Image]({image_url})")
    
    final_display_text = f"✅ Image ready for: **{img_prompt}**"
    status.update(label="Image Generated!", state="complete")

                # --- CASE B: THINKING LOGIC ---
                elif "<thinking>" in full_res:
                    parts = full_res.split("</thinking>")
                    thinking_process = parts[0].replace("<thinking>", "").strip()
                    final_display_text = parts[1].strip()
                    
                    st.write(thinking_process)
                    status.update(label="Thinking Complete!", state="complete")
                
                # --- CASE C: DIRECT COMMANDS ---
                elif "open youtube" in prompt.lower():
                    js_code = '<script>window.open("https://youtube.com", "_blank");</script>'
                    components.html(js_code, height=0)
                    final_display_text = "Opening YouTube in a new tab... 📺"
                    status.update(label="Command Executed", state="complete")
                
                # --- CASE D: NORMAL RESPONSE ---
                else:
                    final_display_text = full_res
                    status.update(label="Done!", state="complete")

            except Exception as e:
                status.update(label="Error!", state="error")
                final_display_text = f"Oops, error aa gaya: {e}"

        # Final UI Update
        st.markdown(final_display_text)
        st.session_state.messages.append({"role": "assistant", "content": final_display_text})
