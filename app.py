import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import random

# --- 1. PREMIUM GEMINI INTERFACE ---
st.set_page_config(page_title="Nexus Flow Ultra v15.5", page_icon="🧠", layout="wide")

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

# --- 2. INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("API Keys missing in Secrets!")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:#1a73e8; text-align:center;'>Nexus Hub ⚡</h3>", unsafe_allow_html=True)
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 4. CHAT HISTORY ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m and m["image"]:
            st.image(m["image"], use_container_width=True)

# --- 5. CHAT ENGINE ---
if prompt := st.chat_input("Ask Nexus Flow..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # SUPER LOGIC SYSTEM PROMPT
            sys_msg = """
            You are Nexus Flow Ultra (Super Logic Mode). 
            - THINKING: Use <thinking> step-by-step logic </thinking> for deep answers.
            - IMAGES: Output ONLY [GENERATE_IMAGE: descriptive prompt in English] for visuals.
            - EMOJIS: Always use suitable emojis. 🚀✨
            - LANGUAGE: Reply in the user's language.
            """
            
            # Using Llama-3.3-70b-specdec (Stable Reasoning Model)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-specdec",
                messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-6:],
                stream=True,
                temperature=0.5
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            # --- PARSING & VISUAL FIX ---
            final_text = full_response
            img_url = None

            # Logic Parser
            if "<thinking>" in full_response:
                parts = full_response.split("</thinking>")
                thought = parts[0].replace("<thinking>","").strip()
                st.markdown(f'<div class="thinking-box">🔍 <b>Super Thinking:</b><br>{thought}</div>', unsafe_allow_html=True)
                final_text = parts[-1].strip()

            # Image Direct Show Parser
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    encoded_p = urllib.parse.quote(img_prompt)
                    # Correct URL logic with random seed for fresh load
                    img_url = f"https://image.pollinations.ai/prompt/{encoded_p}?width=1024&height=1024&nologo=true&seed={random.randint(0, 99999)}"
                    # Cleanup tag from text
                    final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()
                    if not final_text: final_text = "🎨 **Image Generated Successfully:**"

            response_placeholder.markdown(final_text)
            if img_url: 
                st.image(img_url, use_container_width=True)
            
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url})

        except Exception as e:
            st.error(f"Nexus Sync Error: {e} ❌. Try 'llama-3.1-70b-versatile' if this persists.")
            
