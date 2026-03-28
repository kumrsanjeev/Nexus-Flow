import streamlit as st
from groq import Groq
import google.generativeai as genai
import requests
import io
from PIL import Image
import re
import random
import time

# --- 1. PREMIUM GEMINI INTERFACE THEME ---
st.set_page_config(page_title="Nexus Flow Ultra v28", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    [data-testid="stSidebar"] { background-color: #f0f4f9 !important; border-right: none; }
    .stChatMessage { border-radius: 12px; padding: 1.2rem !important; margin-bottom: 1rem; border: 1px solid #f0f2f6 !important; }
    .stChatInputContainer { padding-bottom: 2rem; }
    .stChatInput { border-radius: 26px !important; border: 1px solid #e5e7eb !important; background-color: #f0f4f9 !important; }
    .thinking-box { background-color: #f1f3f4; border-radius: 12px; padding: 15px; color: #1a73e8; border-left: 5px solid #1a73e8; margin-bottom: 10px; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZATION (With Detailed Logging) ---
def load_secrets():
    """Tries to load secrets from Streamlit with clear logging."""
    secrets = {}
    try:
        secrets["groq"] = st.secrets["GROQ_API_KEY"]
        secrets["google"] = st.secrets["GOOGLE_API_KEY"]
        secrets["hf"] = st.secrets["HF_TOKEN"]
        return secrets
    except KeyError as e:
        st.error(f"🚨 Security Alert: Secrets error! Key not found: {e}")
        st.stop()
    except Exception as e:
        st.error(f"🚨 Security Alert: Unable to load secrets: {e}")
        st.stop()

# Loading the secrets once
app_secrets = load_secrets()

# Model Integrations
try:
    groq_client = Groq(api_key=app_secrets["groq"])
    genai.configure(api_key=app_secrets["google"])
except Exception as e:
    st.error(f"🚨 Model Error: Failed to initialize clients: {e}")
    st.stop()

# Hugging Face Stable Diffusion Endpoint
HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HF_HEADERS = {"Authorization": f"Bearer {app_secrets['hf']}"}

# Session State for messages
if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. SIDEBAR (The Control Panel) ---
with st.sidebar:
    st.markdown("<h3 style='color:#1a73e8; text-align:center;'>Nexus Core ⚡</h3>", unsafe_allow_html=True)
    if st.button("➕ New Deep Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 4. HUGGING FACE IMAGE ENGINE (Retry Logic) ---
def generate_hf_image(prompt):
    """Wait and fetch image from Hugging Face"""
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}
    try:
        response = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload, timeout=50)
        
        if response.status_code == 200:
            image_bytes = response.content
            image = Image.open(io.BytesIO(image_bytes))
            return image
        
        elif response.status_code == 503:
            st.warning("⏳ Hugging Face model is warming up... waiting 10 seconds.")
            time.sleep(10)
            return generate_hf_image(prompt) # Retry after sleep
        
        elif response.status_code == 401:
            st.error("🚨 Hugging Face Error 401: Unauthorized. Please check your HF_TOKEN in secrets.")
            return None
        
        else:
            st.error(f"🚨 Image Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"🚨 Image Engine Crash: {e}")
        return None

# --- 5. CHAT DISPLAY ---
if not st.session_state.messages:
    st.markdown("<div class='nexus-title'>Nexus Flow Ultra 🧠</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#5f6368;'>Powered by LLaMA 3.3 for Deep Reasoning & Premium HF Images</p>", unsafe_allow_html=True)
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m and m["image"]:
                st.image(m["image"], use_container_width=True)

# --- 6. CORE LOGIC ---
if prompt := st.chat_input("Message Nexus..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # GROQ TEXT ONLY HISTORY
            clean_history = [
                {"role": m["role"], "content": m["content"]} 
                for m in st.session_state.messages[-8:]
            ]

            sys_msg = """
            You are Nexus Flow Ultra. Use Hinglish naturally.
            - FORMATTING: Answer like ChatGPT. Use bold headings, bullet points, and paragraphs.
            - EMOJIS: Use emojis 🚀.
            - IMAGES: Use [GENERATE_IMAGE: descriptive English prompt] only if asked. Never say you can't.
            """
            
            # Using Llama-3.3-70b-specdec (Stable Reasoning Model)
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-specdec",
                messages=[{"role": "system", "content": sys_msg}] + clean_history,
                stream=True,
                temperature=0.6
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
            # --- IMAGE GENERATION ---
            final_text = full_response
            image_obj = None

            if "<thinking>" in full_response:
                parts = full_response.split("</thinking>")
                # Skip display of reasoning for now unless requested
                final_text = parts[-1].strip()

            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    with st.spinner("⏳ *Creating Premium Image...*"):
                        image_obj = generate_hf_image(img_prompt)
                    
                    # Cleanup tag from text
                    final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()
                    if not final_text: final_text = f"🎨 **Generated your premium image:**"

            response_placeholder.markdown(final_text)
            if image_obj: 
                st.image(image_obj, use_container_width=True)
            
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": image_obj})

        # --- 7. STABLE ERROR HANDLING ---
        except groq_client.APIError as e:
            st.error(f"🚨 Groq API Error: {e}")
            if e.status_code == 401:
                st.warning("Groq unauthorized. Please check your GROQ_API_KEY in secrets.")
                
        except Exception as e:
            st.error(f"Sync Error: {e} ❌. Retrying...")
    
