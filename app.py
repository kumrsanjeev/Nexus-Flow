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
st.set_page_config(page_title="Nexus Flow Ultra v14", page_icon="✨", layout="wide")

# --- API KEYS ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("API Keys missing!")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "db" not in st.session_state:
    st.session_state.db = None

# --- IMAGE GENERATOR (ULTRA FIXED) ---
def generate_image_url(prompt):
    try:
        if not prompt or len(prompt.strip()) < 5:
            return None

        prompt = prompt.strip()
        prompt = re.sub(r'\s+', ' ', prompt)

        # Force better quality
        prompt += ", ultra realistic, 4k, highly detailed, cinematic lighting"

        encoded = urllib.parse.quote_plus(prompt)

        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&seed={random.randint(1,999999)}"

        return url
    except:
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("Nexus Hub ⚡")

    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()

# --- DISPLAY CHAT ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("images"):
            for img in m["images"]:
                st.image(img, use_container_width=True)

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
            You are Nexus AI 🤖
            - Answer in Hinglish
            - Use emojis
            - Clean formatting
            - If visual needed → MUST use [GENERATE_IMAGE: detailed prompt]
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

            # --- 1. AI IMAGE TAG ---
            matches = re.findall(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text, re.DOTALL)

            for m in matches:
                url = generate_image_url(m)
                if url and "pollinations.ai" in url:
                    img_urls.append(url)

            # Remove tags
            final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text, flags=re.DOTALL).strip()

            # --- 2. USER IMAGE INTENT ---
            user_wants_image = any(word in prompt.lower() for word in [
                "image", "photo", "draw", "picture", "generate", "show"
            ])

            if user_wants_image and not img_urls:
                auto_prompt = f"{prompt}, realistic, 4k detailed"
                url = generate_image_url(auto_prompt)
                if url:
                    img_urls.append(url)

            # --- 3. FINAL FALLBACK (ANTI-EMPTY) ---
            if not img_urls:
                fallback_prompt = f"{prompt}, high quality realistic image"
                fallback_url = generate_image_url(fallback_prompt)
                if fallback_url:
                    img_urls.append(fallback_url)

            # Clean text
            final_text = re.sub(r'\n{3,}', '\n\n', final_text)

            response_placeholder.markdown(final_text)

            # --- DISPLAY IMAGES SAFE ---
            valid_imgs = []
            for url in img_urls:
                try:
                    st.image(url, use_container_width=True)
                    valid_imgs.append(url)
                except:
                    st.warning("⚠️ Image failed to load")

            # --- SAVE ---
            st.session_state.messages.append({
                "role": "assistant",
                "content": final_text,
                "images": valid_imgs
            })

        except Exception as e:
            st.error(f"❌ Error: {e}")
