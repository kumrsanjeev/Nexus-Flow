import streamlit as st
from groq import Groq
import google.generativeai as genai
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
    .stChatMessage { background-color: transparent !important; border: none !important; }
    .gemini-greeting { font-size: 3.2rem; font-weight: 500; color: #1f1f1f; margin-top: 80px; text-align: center; }
    .gemini-subtitle { font-size: 3rem; font-weight: 500; color: #c4c7c5; margin-bottom: 50px; text-align: center; }
    .stChatInput { border-radius: 28px !important; background-color: #f0f4f9 !important; border: 1px solid #e5e7eb !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZATION ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:#1a73e8; text-align:center;'>Nexus Core</h3>", unsafe_allow_html=True)
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 4. HOME PAGE ---
if not st.session_state.messages:
    st.markdown("<div class='gemini-greeting'>Hello Sanjeev</div>", unsafe_allow_html=True)
    st.markdown("<div class='gemini-subtitle'>How can I help you today?</div>", unsafe_allow_html=True)
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m and m["image"]:
                st.image(m["image"], use_container_width=True)

# --- 5. CHAT ENGINE (Blank-Image Fixed) ---
if prompt := st.chat_input("Message Nexus..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            # Brain filters history (Only text)
            clean_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-10:]]

            # RE-ADDING EMOJI INSTRUCTIONS
            sys_msg = """You are Nexus AI.
            - EMOJIS: Use 1-2 relevant emojis in every response to keep it friendly. 🚀
            - LANGUAGE: Always mirror the user's language (Hinglish/Hindi).
            - IMAGES: Use ONLY [GENERATE_IMAGE: descriptive English prompt] for visuals.
            """

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + clean_history,
                stream=True,
                temperature=0.75  # Creativity for emojis
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")

            final_text = full_response
            img_url = None

            # HARD-STRICT IMAGE PARSING
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    raw_p = match.group(1).strip()
                    # Safer encoding: keep only alphanumerics & spaces
                    safe_p = re.sub(r'[^a-zA-Z0-9\s]', '', raw_p)
                    encoded = urllib.parse.quote(safe_p, safe='')  # spaces → %20
                    # Smaller size for higher success rate
                    seed = random.randint(1, 999999)
                    ts = int(time.time())  # bust cache
                    img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=768&nologo=true&seed={seed}&t={ts}"

                    final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()

            response_placeholder.markdown(final_text)

            if img_url:
                # Direct Display like Gemini
                st.image(img_url, use_container_width=True)

            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url})

        except Exception as e:
            st.error(f"Nexus Sync Error: {e}")
