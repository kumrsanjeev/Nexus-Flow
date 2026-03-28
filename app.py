import streamlit as st
from groq import Groq
import google.generativeai as genai
import urllib.parse
import re
import random
import time

# --- 1. MINIMALIST UI ---
st.set_page_config(page_title="Nexus Flow Ultra", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    [data-testid="stSidebar"] { background-color: #f0f4f9 !important; border-right: none; }
    .stChatMessage { background-color: transparent !important; border: none !important; padding: 10px 0 !important; }
    .gemini-greeting { font-size: 3.2rem; font-weight: 500; color: #1f1f1f; margin-top: 100px; text-align: center; }
    .gemini-subtitle { font-size: 3rem; font-weight: 500; color: #c4c7c5; margin-bottom: 50px; text-align: center; }
    .stChatInput { border-radius: 28px !important; background-color: #f0f4f9 !important; border: 1px solid #e5e7eb !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZATION ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

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

# --- 5. CHAT ENGINE ---
if prompt := st.chat_input("Message Nexus..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # FIX: Filter history to send ONLY 'role' and 'content' to Groq
            filtered_history = [
                {"role": m["role"], "content": m["content"]} 
                for m in st.session_state.messages[-8:]
            ]

            sys_msg = "You are Nexus Flow Ultra. Match user's language. For images, use ONLY: [GENERATE_IMAGE: descriptive English prompt]. Minimal emojis."
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + filtered_history,
                stream=True,
                temperature=0.7
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            final_text = full_response
            img_url = None

            # Image Logic
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    clean_p = re.sub(r'[^a-zA-Z0-9\s]', '', img_prompt)
                    encoded = urllib.parse.quote(clean_p)
                    img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={random.randint(1, 999999)}"
                    final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()

            response_placeholder.markdown(final_text)
            if img_url:
                time.sleep(1)
                st.image(img_url, use_container_width=True)
            
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url})

        except Exception as e:
            st.error(f"Error: {e}")
            
