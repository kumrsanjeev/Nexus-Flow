import streamlit as st
from groq import Groq
import google.generativeai as genai
import requests
import io
from PIL import Image
import re
import random

# --- 1. MINIMAL UI ---
st.set_page_config(page_title="Nexus Flow Ultra", page_icon="🤖", layout="wide")

# --- 2. INITIALIZATION ---
HF_TOKEN = st.secrets.get("HF_TOKEN")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Hugging Face Premium Model
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. IMAGE GENERATOR ---
def get_image(prompt):
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=40)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        return None
    except:
        return None

# --- 4. DISPLAY CHAT ---
if not st.session_state.messages:
    st.markdown("<h1 style='text-align:center; margin-top:100px;'>Hello Sanjeev</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:gray;'>How can I help you?</h2>", unsafe_allow_html=True)
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m and m["image"]:
                st.image(m["image"], use_container_width=True)

# --- 5. CHAT LOGIC ---
if prompt := st.chat_input("Message Nexus..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        res_placeholder = st.empty()
        full_res = ""
        
        # History filter (Text only)
        clean_hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-8:]]
        
        sys_msg = "You are Nexus AI. Use minimal emojis. For images, use ONLY: [GENERATE_IMAGE: descriptive prompt]."
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": sys_msg}] + clean_hist,
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
                with st.spinner("🎨 Creating Premium Image..."):
                    image_obj = get_image(img_prompt)
                final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()

        res_placeholder.markdown(final_text)
        if image_obj:
            st.image(image_obj, use_container_width=True)
        
        st.session_state.messages.append({"role": "assistant", "content": final_text, "image": image_obj})
    
