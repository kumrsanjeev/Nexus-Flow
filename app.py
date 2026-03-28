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

# --- 1. PREMIUM GEMINI INTERFACE ---
st.set_page_config(page_title="Nexus Flow Ultra", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    [data-testid="stSidebar"] { background-color: #f0f4f9 !important; border-right: none; }
    .stChatMessage { background-color: transparent !important; border: none !important; padding: 10px 0 !important; }
    
    /* Clean Greeting Style */
    .gemini-greeting { font-size: 3rem; font-weight: 500; color: #1f1f1f; margin-top: 60px; text-align: center; }
    .gemini-subtitle { font-size: 2.8rem; font-weight: 500; color: #c4c7c5; margin-bottom: 50px; text-align: center; }
    
    .thinking-box { background-color: #f0f7ff; border-radius: 12px; padding: 15px; color: #0056b3; border-left: 5px solid #0056b3; margin: 10px 0; }
    .stChatInput { border-radius: 30px !important; background-color: #f0f4f9 !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:#1a73e8; text-align:center;'>Nexus Hub ⚡</h3>", unsafe_allow_html=True)
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 4. GEMINI HOME PAGE ---
if not st.session_state.messages:
    st.markdown("<div class='gemini-greeting'>Hello Sanjeev</div>", unsafe_allow_html=True)
    st.markdown("<div class='gemini-subtitle'>How can I help you?</div>", unsafe_allow_html=True)
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m and m["image"]:
                st.image(m["image"], use_container_width=True)

# --- 5. CHAT ENGINE (Mirroring + Image) ---
if prompt := st.chat_input("Message Nexus..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # STRICT Mirroring & Visual Rules
            sys_msg = """
            You are Nexus Flow Ultra. 
            - LANGUAGE MIRRORING: Always reply in the user's language (Hinglish/Hindi/English). 
            - EMOJIS: Use emojis in every single reply. 🚀✨
            - IMAGE GENERATION: If asked for an image, reply with a short confirmation in user's language AND the tag: [GENERATE_IMAGE: descriptive English prompt].
            - DO NOT say "I am a text model".
            """
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-8:],
                stream=True,
                temperature=0.8
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            # --- FINAL PARSING ---
            final_text = full_response
            img_url = None

            # 1. Thinking Logic Box (if any)
            if "<thinking>" in full_response:
                parts = full_response.split("</thinking>")
                st.markdown(f'<div class="thinking-box">🔍 <b>Thinking:</b><br>{parts[0].replace("<thinking>","").strip()}</div>', unsafe_allow_html=True)
                final_text = parts[-1].strip()

            # 2. Image Logic (Direct Show & Hide Tag)
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    # CLEANING PROMPT
                    clean_p = re.sub(r'[^a-zA-Z0-9\s]', '', img_prompt)
                    encoded = urllib.parse.quote(clean_p)
                    # UNIVERSAL STABLE LINK
                    seed = random.randint(1, 999999)
                    img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}"
                    # HIDE THE TAG FROM USER
                    final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()

            response_placeholder.markdown(final_text)
            if img_url: 
                time.sleep(1) # Wait for server
                st.image(img_url, use_container_width=True)
            
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url})

        except Exception as e:
            st.error(f"Error: {e}")
