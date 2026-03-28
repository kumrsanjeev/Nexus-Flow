import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import random

# --- CONFIG ---
st.set_page_config(page_title="Nexus Flow Ultra v13", page_icon="✨", layout="wide")

# --- KEYS ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("API Keys missing!")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# --- STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "db" not in st.session_state:
    st.session_state.db = None

# --- IMAGE FUNCTION ---
def generate_image_url(prompt):
    try:
        prompt = prompt.strip()

        if len(prompt) < 5:
            return None

        prompt = re.sub(r'[^\w\s,.-]', '', prompt)
        encoded = urllib.parse.quote(prompt)

        return f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&seed={random.randint(0,999999)}"
    except:
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("Nexus Hub ⚡")

    if st.button("New Chat"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()

# --- CHAT DISPLAY ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("images"):
            for img in m["images"]:
                st.image(img)

# --- CHAT INPUT ---
if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            # SYSTEM PROMPT
            sys_msg = """
            You are Nexus AI.
            - Answer in Hinglish
            - Use emojis
            - Use clean formatting
            - If image needed, use: [GENERATE_IMAGE: detailed prompt]
            """

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] +
                         [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-10:]],
                stream=True
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")

            final_text = full_response
            img_urls = []

            # --- 🔥 1. AI GENERATED IMAGE TAG ---
            matches = re.findall(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text, re.DOTALL)

            for m in matches:
                url = generate_image_url(m)
                if url:
                    img_urls.append(url)

            final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text, flags=re.DOTALL).strip()

            # --- 🔥 2. USER COMMAND IMAGE DETECTION ---
            user_wants_image = any(word in prompt.lower() for word in [
                "image", "photo", "draw", "picture", "generate image", "show image"
            ])

            if user_wants_image and not img_urls:
                auto_prompt = f"{prompt}, high quality, detailed, realistic"
                url = generate_image_url(auto_prompt)
                if url:
                    img_urls.append(url)

            # --- CLEAN TEXT ---
            final_text = re.sub(r'\n{3,}', '\n\n', final_text)

            response_placeholder.markdown(final_text)

            # --- SHOW IMAGES ---
            for url in img_urls:
                st.image(url, use_container_width=True)

            # --- SAVE ---
            st.session_state.messages.append({
                "role": "assistant",
                "content": final_text,
                "images": img_urls
            })

        except Exception as e:
            st.error(f"Error: {e}")
