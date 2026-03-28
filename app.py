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

# --- 1. MINIMALIST GEMINI UI ---
st.set_page_config(page_title="Nexus Flow Ultra", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    [data-testid="stSidebar"] { background-color: #f0f4f9 !important; border-right: none; }
    .stChatMessage { background-color: transparent !important; border: none !important; padding: 10px 0 !important; }
    
    /* Clean Center Greeting */
    .gemini-greeting { font-size: 3.2rem; font-weight: 500; color: #1f1f1f; margin-top: 100px; text-align: center; }
    .gemini-subtitle { font-size: 3rem; font-weight: 500; color: #c4c7c5; margin-bottom: 50px; text-align: center; }
    
    .thinking-box { background-color: #f8f9fa; border-radius: 10px; padding: 15px; color: #444746; border-left: 4px solid #1a73e8; margin: 10px 0; font-size: 0.9rem; }
    .stChatInput { border-radius: 28px !important; background-color: #f0f4f9 !important; border: 1px solid #e5e7eb !important; }
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
    st.markdown("<h3 style='color:#1a73e8; text-align:center;'>Nexus Hub</h3>", unsafe_allow_html=True)
    if st.button("➕ New Conversation"):
        st.session_state.messages = []
        st.rerun()

# --- 4. HOME PAGE ---
if not st.session_state.messages:
    st.markdown("<div class='gemini-greeting'>Hello Sanjeev</div>", unsafe_allow_html=True)
    st.markdown("<div class='gemini-subtitle'>How can I help you?</div>", unsafe_allow_html=True)
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m and m["image"]:
                st.image(m["image"], use_container_width=True)

# --- 5. CHAT ENGINE (Strict & Minimal) ---
if prompt := st.chat_input("Message Nexus..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # STRICT Minimalist Rules
            sys_msg = """
            You are Nexus Flow Ultra. 
            - EMOJIS: Use very few, only if necessary. Keep it professional.
            - LANGUAGE: Match the user's language (Hinglish/Hindi/English). 
            - IMAGES: Reply with a brief confirmation and ONLY the tag: [GENERATE_IMAGE: descriptive English prompt].
            - FORMATTING: Use clean headings and bullet points.
            """
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-8:],
                stream=True,
                temperature=0.7
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            # --- FINAL PARSING ---
            final_text = full_response
            img_url = None

            # Thinking Parser
            if "<thinking>" in full_response:
                parts = full_response.split("</thinking>")
                st.markdown(f'<div class="thinking-box"><b>Reasoning:</b><br>{parts[0].replace("<thinking>","").strip()}</div>', unsafe_allow_html=True)
                final_text = parts[-1].strip()

            # Image Direct Logic
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    # Clean and Encode URL
                    clean_p = re.sub(r'[^a-zA-Z0-9\s]', '', img_prompt)
                    encoded = urllib.parse.quote(clean_p)
                    # Use unique seed for fresh generation
                    img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={random.randint(1, 999999)}"
                    # REMOVE TAG FROM CHAT OUTPUT
                    final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()
                    if not final_text: final_text = "Generated your requested image:"

            response_placeholder.markdown(final_text)
            if img_url: 
                time.sleep(1) # Ensuring server side sync
                st.image(img_url, use_container_width=True)
            
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url})

        except Exception as e:
            st.error(f"Error: {e}")
            
