import streamlit as st
from groq import Groq
import google.generativeai as genai
import requests
import io
from PIL import Image
import re
import time

# --- 1. MINIMAL UI ---
st.set_page_config(page_title="Nexus Flow Ultra", layout="wide")

# --- 2. SECURE INITIALIZATION ---
# Dashboard > Settings > Secrets mein ORIGINAL keys daalein
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
    GOOGLE_KEY = st.secrets["GOOGLE_API_KEY"]
    HF_TOKEN = st.secrets["HF_TOKEN"]
except:
    st.error("🚨 API Keys missing in Streamlit Secrets!")
    st.stop()

client = Groq(api_key=GROQ_KEY)
genai.configure(api_key=GOOGLE_KEY)

# Hugging Face Config
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# --- 3. ROBUST IMAGE FETCHING ---
def fetch_image(prompt):
    """Wait and fetch image from Hugging Face"""
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        elif response.status_code == 503:
            st.warning("⏳ Model is loading... trying again in 5 seconds.")
            time.sleep(5)
            return fetch_image(prompt) # Retry once
        return None
    except Exception as e:
        return None

# --- 4. CHAT LOGIC ---
if "messages" not in st.session_state: st.session_state.messages = []

# Minimalist Home Page
if not st.session_state.messages:
    st.markdown("<h1 style='text-align:center;'>Hello Sanjeev</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:gray;'>How can I help you?</h3>", unsafe_allow_html=True)
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m and m["image"]:
                st.image(m["image"], use_container_width=True)

if prompt := st.chat_input("Message Nexus..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        res_placeholder = st.empty()
        full_res = ""
        
        # Text-only history for Groq
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-6:]]
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "You are Nexus. For images, use [GENERATE_IMAGE: prompt]. Match user's language."}] + history,
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
                with st.spinner("🎨 Hugging Face is generating..."):
                    image_obj = fetch_image(img_prompt)
                final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()

        res_placeholder.markdown(final_text)
        if image_obj:
            st.image(image_obj, use_container_width=True)
        
        st.session_state.messages.append({"role": "assistant", "content": final_text, "image": image_obj})
    
