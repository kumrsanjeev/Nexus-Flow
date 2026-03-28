import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import random
import requests
import io
from PIL import Image

# --- 1. PREMIUM GEMINI INTERFACE THEME ---
st.set_page_config(page_title="Nexus Flow Ultra v16", page_icon="🧠", layout="wide")

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

# --- 2. API KEYS INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")
hf_token = st.secrets.get("HF_TOKEN") # Mandatory for v16

if not groq_key or not google_key or not hf_token:
    st.error("API Keys missing in Secrets! (GROQ, GOOGLE, HF_TOKEN)")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# Hugging Face API Config (Stable Diffusion XL)
HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {hf_token}"}

if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:#1a73e8; text-align:center;'>Nexus Hub ⚡</h3>", unsafe_allow_html=True)
    if st.button("➕ New Conversation"):
        st.session_state.messages = []
        st.rerun()

# --- 4. HUGGING FACE IMAGE GENERATOR FUNCTION ---
def generate_hf_image(prompt):
    """Fetches image from Hugging Face Inference API"""
    try:
        # Step 1: Clean prompt (remove emojis, bad chars)
        clean_prompt = re.sub(r'[^\x00-\x7F]+', '', prompt).strip()
        
        # Step 2: Make API Request
        response = requests.post(HF_API_URL, headers=headers, json={"inputs": clean_prompt}, timeout=30)
        
        # Step 3: Parse Image Data
        if response.status_code == 200:
            image_bytes = response.content
            image = Image.open(io.BytesIO(image_bytes))
            return image
        elif response.status_code == 503: # Model is loading
            return "LOADING"
        else:
            return f"ERROR: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"CRASH: {e}"

# --- 5. CHAT DISPLAY ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m and m["image"]:
            st.image(m["image"], use_container_width=True)

# --- 6. CORE CHAT ENGINE ---
if prompt := st.chat_input("Deeply analyze this..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            sys_msg = """You are Nexus Flow Ultra (Hugging Face Image Mode). 
            Use <thinking> step-by-step logic </thinking> for deep answers.
            For visual requests, use ONLY: [GENERATE_IMAGE: highly descriptive English prompt].
            Maintain natural Hinglish and emojis."""
            
            # Streaming from Llama 3.3 Versatile
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-8:],
                stream=True,
                temperature=0.6
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            # --- PARSING & VISUAL ENGINE FIXED ---
            final_text = full_response
            image_data = None # Holds the actual PIL image object

            # 1. Super Logic Box
            if "<thinking>" in full_response:
                parts = full_response.split("</thinking>")
                thought = parts[0].replace("<thinking>","").strip()
                st.markdown(f'<div class="thinking-box">🔍 <b>Super Thinking:</b><br>{thought}</div>', unsafe_allow_html=True)
                final_text = parts[-1].strip()

            # 2. HUGGING FACE IMAGE LOGIC
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    st.write(f"⏳ *Generating Premium Image for:* **{img_prompt}**...")
                    
                    # Call Hugging Face
                    image_result = generate_hf_image(img_prompt)
                    
                    if isinstance(image_result, Image.Image): # Success
                        image_data = image_result
                        final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()
                        if not final_text: final_text = f"🎨 **Generated by Stable Diffusion XL:**"
                    elif image_result == "LOADING":
                        final_text = "Hugging Face is still loading the model. Try again in 1 minute."
                        image_data = None
                    else: # Error
                        st.error(f"Image Error: {image_result}")
                        image_data = None

            response_placeholder.markdown(final_text)
            if image_data: 
                st.image(image_data, use_container_width=True)
            
            # Session history saving
            if image_data:
                st.session_state.messages.append({"role": "assistant", "content": final_text, "image": image_data})
            else:
                st.session_state.messages.append({"role": "assistant", "content": final_text})

        except Exception as e:
            st.error(f"Sync Error: {e} ❌. Reverting to basic image engine if HF persists.")
            
