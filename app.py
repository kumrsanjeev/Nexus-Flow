import streamlit as st
from groq import Groq
import google.generativeai as genai
import requests
import io
from PIL import Image
import re
import time

# --- 1. PREMIUM MINIMAL UI ---
st.set_page_config(page_title="Nexus Flow Ultra", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    [data-testid="stSidebar"] { background-color: #f0f4f9 !important; border-right: none; }
    .stChatMessage { background-color: transparent !important; border: none !important; }
    .gemini-greeting { font-size: 3.2rem; font-weight: 500; color: #1f1f1f; margin-top: 80px; text-align: center; }
    .gemini-subtitle { font-size: 3rem; font-weight: 500; color: #c4c7c5; margin-bottom: 50px; text-align: center; }
    .stChatInput { border-radius: 28px !important; background-color: #f0f4f9 !important; border: 1px solid #e5e7eb !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZATION ---
HF_TOKEN = st.secrets.get("HF_TOKEN")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Hugging Face API Config
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:#1a73e8; text-align:center;'>Nexus Hub</h3>", unsafe_allow_html=True)
    if st.button("➕ New Conversation"):
        st.session_state.messages = []
        st.rerun()

# --- 4. HUGGING FACE IMAGE FUNCTION ---
def query_hf(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.content
    return None

# --- 5. HOME PAGE ---
if not st.session_state.messages:
    st.markdown("<div class='gemini-greeting'>Hello Sanjeev</div>", unsafe_allow_html=True)
    st.markdown("<div class='gemini-subtitle'>How can I help you?</div>", unsafe_allow_html=True)
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m and m["image"]:
                st.image(m["image"], use_container_width=True)

# --- 6. CHAT ENGINE ---
if prompt := st.chat_input("Message Nexus..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # Brain filters history (Only text)
            clean_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-8:]]

            sys_msg = "You are Nexus AI. Use Hinglish. For images, use ONLY: [GENERATE_IMAGE: descriptive English prompt]. No extra text in image replies."
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + clean_history,
                stream=True,
                temperature=0.7
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            final_text = full_response
            image_obj = None

            # IMAGE LOGIC
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    with st.spinner("🎨 Creating high-quality image..."):
                        image_bytes = query_hf({"inputs": img_prompt})
                        if image_bytes:
                            image_obj = Image.open(io.BytesIO(image_bytes))
                    
                    final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()

            response_placeholder.markdown(final_text)
            if image_obj:
                st.image(image_obj, use_container_width=True)
            
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": image_obj})

        except Exception as e:
            st.error(f"Error: {e}")
                    
