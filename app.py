import streamlit as st
import google.generativeai as genai
import urllib.parse
import re

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Nexus Flow Pro 🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .thinking-box { background-color: #1a1c23; border-left: 4px solid #00ffcc; padding: 10px; margin: 10px 0; color: #00ffcc; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API SETUP ---
def initialize_agent():
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ API Key missing! Check Streamlit Secrets.")
        return None
    
    genai.configure(api_key=api_key)
    
    # Generic AI Instruction with Thinking & Image support
    instruction = """
    You are Nexus Flow AI. 
    1. IMAGE: If user asks for an image, respond ONLY with: [GENERATE_IMAGE: descriptive prompt in English]
    2. THINKING: For complex tasks (Coding/Math), use <thinking> step-by-step logic </thinking> then the final answer.
    3. LANGUAGE: Use Hinglish.
    """
    
    # Fixed model name to avoid 404 error
    return genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=instruction)

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_model" not in st.session_state:
    st.session_state.chat_model = initialize_agent()

# --- 4. UI DISPLAY ---
st.title("Nexus Flow Pro 🤖")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m:
            st.image(m["image"])

# --- 5. CHAT LOGIC ---
if prompt := st.chat_input("Kaise help karu Sanjeev?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if st.session_state.chat_model:
        with st.chat_message("assistant"):
            try:
                # Chat History format for Gemini
                history = [{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
                chat = st.session_state.chat_model.start_chat(history=history)
                response = chat.send_message(prompt)
                full_res = response.text
                
                final_text = full_res
                img_url = None

                # Parsing Thinking Tags
                if "<thinking>" in full_res:
                    parts = full_res.split("</thinking>")
                    thought = parts[0].replace("<thinking>", "").strip()
                    final_text = parts[1].strip()
                    st.markdown(f'<div class="thinking-box"><b>🧠 Logic Tree:</b><br>{thought}</div>', unsafe_allow_html=True)

                # Parsing Image Generation
                if "[GENERATE_IMAGE:" in final_text:
                    match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                    if match:
                        img_prompt = match.group(1).strip()
                        encoded_prompt = urllib.parse.quote(img_prompt)
                        img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
                        final_text = f"🎨 **Visualizing:** {img_prompt}"

                st.markdown(final_text)
                if img_url:
                    st.image(img_url)
                
                # Save to history
                msg_data = {"role": "assistant", "content": final_text}
                if img_url: msg_data["image"] = img_url
                st.session_state.messages.append(msg_data)

            except Exception as e:
                st.error(f"Error: {str(e)}")
