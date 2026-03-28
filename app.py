import streamlit as st
from groq import Groq
import google.generativeai as genai
import requests
import io
from PIL import Image
import re
import random
import time

# --- 1. GEMINI UI THEME ---
st.set_page_config(page_title="Nexus Flow Ultra", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    [data-testid="stSidebar"] { background-color: #f0f4f9 !important; border-right: none; }
    .stChatMessage { border-radius: 12px; padding: 1.2rem !important; margin-bottom: 1rem; border: 1px solid #f0f2f6 !important; }
    .stChatInput { border-radius: 26px !important; border: 1px solid #e5e7eb !important; background-color: #f0f4f9 !important; }
    .gemini-greeting { font-size: 3rem; font-weight: 500; color: #1f1f1f; margin-top: 60px; text-align: center; }
    .gemini-subtitle { font-size: 2.8rem; font-weight: 500; color: #c4c7c5; margin-bottom: 40px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZATION ---
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
    GOOGLE_KEY = st.secrets["GOOGLE_API_KEY"]
    HF_TOKEN = st.secrets["HF_TOKEN"]
except Exception as e:
    st.error("🚨 API Keys missing in Secrets!")
    st.stop()

client = Groq(api_key=GROQ_KEY)
genai.configure(api_key=GOOGLE_KEY)

# Using a more reliable HF Model
HF_API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:#1a73e8; text-align:center;'>Nexus Core ⚡</h3>", unsafe_allow_html=True)
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 4. RELIABLE IMAGE FUNCTION ---
def make_image(prompt):
    """Retries until model is ready"""
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}
    for attempt in range(3): # Try 3 times
        try:
            res = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload, timeout=60)
            if res.status_code == 200:
                return Image.open(io.BytesIO(res.content))
            elif res.status_code == 503:
                time.sleep(10) # Wait if model is loading
                continue
            else:
                return None
        except:
            continue
    return None

# --- 5. CHAT DISPLAY ---
if not st.session_state.messages:
    st.markdown("<div class='gemini-greeting'>Hello Sanjeev</div>", unsafe_allow_html=True)
    st.markdown("<div class='gemini-subtitle'>How can I help you today?</div>", unsafe_allow_html=True)
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
        res_placeholder = st.empty()
        full_res = ""
        
        try:
            hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-8:]]
            sys_msg = "You are Nexus. Match user's language. Use ONLY [GENERATE_IMAGE: prompt in English] for images."
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + hist,
                stream=True
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    res_placeholder.markdown(full_res + "▌")
            
            final_text = full_res
            image_obj = None

            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    with st.spinner("⏳ Creating Image (it may take 20s)..."):
                        image_obj = make_image(img_prompt)
                    final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()

            res_placeholder.markdown(final_text)
            if image_obj:
                st.image(image_obj, use_container_width=True)
                st.session_state.messages.append({"role": "assistant", "content": final_text, "image": image_obj})
            else:
                st.session_state.messages.append({"role": "assistant", "content": final_text})

        except Exception as e:
            st.error(f"Error: {e}")
