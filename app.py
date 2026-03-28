import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import random
import time

# --- 1. PREMIUM GEMINI UI ---
st.set_page_config(page_title="Nexus Flow Ultra v19.5", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    [data-testid="stSidebar"] { background-color: #f0f4f9 !important; border-right: none; }
    .stChatMessage { background-color: transparent !important; border: none !important; padding: 10px 0 !important; }
    
    .stButton>button {
        background-color: #ffffff !important;
        color: #444746 !important;
        border: 1px solid #c4c7c5 !important;
        border-radius: 25px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        width: 100%;
        text-align: left !important;
    }
    .stButton>button:hover { border-color: #1a73e8 !important; background-color: #f8f9ff !important; }

    .gemini-greeting { font-size: 3rem; font-weight: 500; color: #1f1f1f; margin-top: 60px; }
    .gemini-subtitle { font-size: 2.8rem; font-weight: 500; color: #c4c7c5; margin-bottom: 40px; }
    
    .thinking-box { background-color: #f0f7ff; border-radius: 12px; padding: 15px; color: #0056b3; border-left: 5px solid #0056b3; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

if "messages" not in st.session_state: st.session_state.messages = []
if "db" not in st.session_state: st.session_state.db = None

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:#1a73e8; text-align:center;'>Nexus Hub ⚡</h3>", unsafe_allow_html=True)
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()

# --- 4. GEMINI HOME PAGE ---
if not st.session_state.messages:
    st.markdown("<div class='gemini-greeting'>Hi Sanjeev</div>", unsafe_allow_html=True)
    st.markdown("<div class='gemini-subtitle'>Where should we start?</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🖼️ **Create:** A high-quality image of a cute cat"):
            st.session_state.messages.append({"role":"user", "content":"Create image of a cute cat"})
            st.rerun()
    with col2:
        if st.button("🧠 **Explain:** Refraction of light in simple words"):
            st.session_state.messages.append({"role":"user", "content":"Explain refraction of light deeply in Hinglish"})
            st.rerun()
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m and m["image"]:
                st.image(m["image"], use_container_width=True)

# --- 5. CHAT ENGINE ---
if prompt := st.chat_input("Ask Nexus..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            sys_msg = """You are Nexus Flow Ultra. 
            - IMAGES: Use ONLY [GENERATE_IMAGE: prompt] for photos.
            - LOGIC: Use <thinking> step-by-step logic </thinking> for deep answers.
            - EMOJIS: Use relevant emojis 🚀✨.
            """
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-8:]],
                stream=True,
                temperature=0.6
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            # --- PARSING & IMAGE FIX ---
            final_text = full_response
            img_url = None

            if "<thinking>" in full_response:
                parts = full_response.split("</thinking>")
                st.markdown(f'<div class="thinking-box">🔍 <b>Thinking:</b><br>{parts[0].replace("<thinking>","").strip()}</div>', unsafe_allow_html=True)
                final_text = parts[-1].strip()

            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    # CLEAN PROMPT FOR URL
                    clean_p = re.sub(r'[^\w\s]', '', img_prompt)
                    encoded = urllib.parse.quote(clean_p)
                    # ADDING TIMESTAMP TO PREVENT BLANK CACHE
                    t_stamp = int(time.time())
                    img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={random.randint(0, 99999)}&t={t_stamp}"
                    final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()

            response_placeholder.markdown(final_text)
            if img_url:
                # Add a small delay to ensure server readiness
                time.sleep(1)
                st.image(img_url, use_container_width=True)
            
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url})

        except Exception as e:
            st.error(f"Error: {e}")
            
