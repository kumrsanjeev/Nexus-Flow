import streamlit as st
import google.generativeai as genai
from groq import Groq
import requests
import io
from PIL import Image
import re
import time

# --- 1. PREMIUM UI THEME ---
st.set_page_config(page_title="Nexus Flow Ultra v32", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    [data-testid="stSidebar"] { background-color: #f0f4f9 !important; }
    .stChatMessage { border-radius: 12px; padding: 1rem !important; }
    .stChatInput { border-radius: 30px !important; background-color: #f0f4f9 !important; border: none !important; }
    .gemini-greeting { font-size: 3rem; font-weight: 500; color: #1f1f1f; margin-top: 60px; text-align: center; }
    .gemini-subtitle { font-size: 2.8rem; font-weight: 500; color: #c4c7c5; margin-bottom: 40px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZATION ---
try:
    GOOGLE_KEY = st.secrets["GOOGLE_API_KEY"]
    HF_TOKEN = st.secrets["HF_TOKEN"]
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("🚨 Secrets missing! Check GOOGLE_API_KEY, HF_TOKEN, and GROQ_API_KEY.")
    st.stop()

# Models
genai.configure(api_key=GOOGLE_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")
groq_client = Groq(api_key=GROQ_KEY)

# Hugging Face Config (Stability AI)
HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. HUGGING FACE IMAGE FUNCTION ---
def generate_hf_image(prompt):
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        return None
    except:
        return None

# --- 4. DISPLAY ---
if not st.session_state.messages:
    st.markdown("<div class='gemini-greeting'>Hello Sanjeev</div>", unsafe_allow_html=True)
    st.markdown("<div class='gemini-subtitle'>Nexus is now powered by Hugging Face & Gemini</div>", unsafe_allow_html=True)
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m and m["image"]:
                st.image(m["image"], use_container_width=True)

# --- 5. CORE LOGIC ---
if prompt := st.chat_input("Message Nexus..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        res_placeholder = st.empty()
        
        # ChatGPT-like logic and thinking using Gemini
        sys_prompt = "You are Nexus AI. Use Hinglish. Answer professionally like ChatGPT. For images, use ONLY [GENERATE_IMAGE: descriptive prompt]."
        chat_response = gemini_model.generate_content(f"{sys_prompt}\nUser: {prompt}")
        full_res = chat_response.text
        
        final_text = full_res
        image_obj = None

        # Image parsing
        if "[GENERATE_IMAGE:" in final_text:
            match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
            if match:
                img_prompt = match.group(1).strip()
                with st.spinner("🎨 Hugging Face is drawing..."):
                    image_obj = generate_hf_image(img_prompt)
                final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()

        res_placeholder.markdown(final_text)
        if image_obj:
            st.image(image_obj, use_container_width=True)
        
        st.session_state.messages.append({"role": "assistant", "content": final_text, "image": image_obj})
        
