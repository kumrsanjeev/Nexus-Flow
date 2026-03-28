import streamlit as st
from groq import Groq
import google.generativeai as genai
import urllib.parse
import re
import random
import requests
import time

# --- CONFIG ---
st.set_page_config(page_title="Nexus Flow Ultra v15", page_icon="✨", layout="wide")

# --- API KEYS ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("API Keys missing!")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# --- SESSION ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 🔥 IMAGE GENERATOR WITH VALIDATION ---
def generate_image_url(prompt, retries=3):
    if not prompt or len(prompt.strip()) < 5:
        return None

    prompt = re.sub(r'\s+', ' ', prompt.strip())
    prompt += ", ultra realistic, 4k, highly detailed"

    for _ in range(retries):
        try:
            encoded = urllib.parse.quote_plus(prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&seed={random.randint(1,999999)}"

            # 🔥 CHECK IF IMAGE REALLY EXISTS
            res = requests.head(url, timeout=5)

            if res.status_code == 200:
                return url

        except:
            pass

        time.sleep(1)

    return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("Nexus Hub ⚡")
    if st.button("New Chat"):
        st.session_state.messages = []
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
            - Hinglish me answer do
            - Emojis use karo
            - Clean formatting
            - Agar visual useful ho → [GENERATE_IMAGE: detailed prompt] zaroor use karo
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

            # --- AI TAG IMAGE ---
            matches = re.findall(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text, re.DOTALL)

            for m in matches:
                url = generate_image_url(m)
                if url:
                    img_urls.append(url)

            final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text, flags=re.DOTALL).strip()

            # --- USER IMAGE INTENT ---
            if any(word in prompt.lower() for word in ["image", "photo", "draw", "picture"]):
                if not img_urls:
                    url = generate_image_url(prompt)
                    if url:
                        img_urls.append(url)

            # --- FINAL FALLBACK ---
            if not img_urls:
                fallback = generate_image_url("beautiful high quality scene")
                if fallback:
                    img_urls.append(fallback)

            # --- SHOW TEXT ---
            response_placeholder.markdown(final_text)

            # --- SHOW ONLY VALID IMAGES ---
            valid_images = []
            for url in img_urls:
                try:
                    st.image(url, use_container_width=True)
                    valid_images.append(url)
                except:
                    pass

            # --- SAVE ---
            st.session_state.messages.append({
                "role": "assistant",
                "content": final_text,
                "images": valid_images
            })

        except Exception as e:
            st.error(f"❌ Error: {e}")
