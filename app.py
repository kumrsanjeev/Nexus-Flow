import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import random

# --- 1. PREMIUM UI ---
st.set_page_config(page_title="Nexus Flow Ultra v15", page_icon="🧠", layout="wide")
st.markdown("""<style>
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    .thinking-box { background-color: #f0f7ff; border-radius: 12px; padding: 15px; color: #0056b3; border-left: 5px solid #0056b3; margin: 10px 0; font-family: 'Courier New', monospace; font-size: 0.85rem; }
    .stChatMessage { border-radius: 15px; border: 1px solid #eef2f6 !important; margin-bottom: 10px; }
    .stChatInput { border-radius: 30px !important; }
</style>""", unsafe_allow_html=True)

# --- 2. INITIALIZATION ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. MAIN CHAT ENGINE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m and m["image"]: st.image(m["image"], use_container_width=True)

if prompt := st.chat_input("Deeply analyze this..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        res_placeholder = st.empty()
        full_res = ""
        
        # --- SUPER THINKING PROMPT ---
        sys_msg = """
        You are Nexus Flow Ultra in 'Super Thinking' Mode. 
        - STRATEGY: Before answering, you MUST think step-by-step. 
        - FORMAT: Start your internal logic with <thinking> and end with </thinking>. 
        - DEPTH: If a question is scientific or logical, break it down like a professor.
        - IMAGES: Output ONLY [GENERATE_IMAGE: descriptive English prompt] for visuals.
        - EMOJIS: Use emojis for a friendly Gemini vibe 🚀.
        """
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-6:],
            stream=True,
            temperature=0.4 # Logic ke liye temperature kam rakha hai (Deep Thinking)
        )

        for chunk in completion:
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                res_placeholder.markdown(full_res + "▌")
        
        # --- PARSING LOGIC ---
        final_ans = full_res
        img_url = None

        # 1. Thinking Box Display
        if "<thinking>" in full_res:
            parts = full_res.split("</thinking>")
            thought = parts[0].replace("<thinking>","").strip()
            st.markdown(f'<div class="thinking-box"><b>🧠 Super Thinking:</b><br>{thought}</div>', unsafe_allow_html=True)
            final_ans = parts[-1].strip()

        # 2. Image Direct Show Fix
        if "[GENERATE_IMAGE:" in full_res:
            match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', full_res)
            if match:
                img_prompt = match.group(1).strip()
                encoded = urllib.parse.quote(img_prompt)
                img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={random.randint(0, 9999)}"
                final_ans = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_ans).strip()

        res_placeholder.markdown(final_ans)
        if img_url: st.image(img_url, use_container_width=True)
        st.session_state.messages.append({"role": "assistant", "content": final_ans, "image": img_url})
        
