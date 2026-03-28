import streamlit as st
from groq import Groq
import google.generativeai as genai
import urllib.parse
import re
import random
import time

# --- 1. CLEAN MINIMAL INTERFACE ---
st.set_page_config(page_title="Nexus Flow Ultra", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    [data-testid="stSidebar"] { background-color: #f0f4f9 !important; border-right: none; }
    .stChatMessage { background-color: transparent !important; border: none !important; }
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

# --- 5. CHAT ENGINE (Separated Tasks) ---
if prompt := st.chat_input("Message Nexus..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # TASK 1: Brain (Groq) only sees Text History
            clean_history = [
                {"role": m["role"], "content": m["content"]} 
                for m in st.session_state.messages[-8:]
            ]

            sys_msg = """You are Nexus AI. 
            STRICT RULE 1: For images, output ONLY: [GENERATE_IMAGE: descriptive English prompt].
            STRICT RULE 2: Keep conversation in user's language.
            STRICT RULE 3: No extra talking when generating images."""
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + clean_history,
                stream=True,
                temperature=0.6
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            # TASK 2: Manager (Parsing Logic)
            final_text = full_response
            img_url = None

            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    # TASK 3: Artist (Pollinations) generates Unique Stable Link
                    raw_prompt = match.group(1).strip()
                    # Hard cleanup for URL safety
                    safe_prompt = re.sub(r'[^a-zA-Z0-9\s]', '', raw_prompt)
                    encoded = urllib.parse.quote(safe_prompt)
                    
                    # Force unique seed and cache-busting timestamp
                    img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={random.randint(1, 1000000)}"
                    
                    # Clean the UI: Hide the tag
                    final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()
                    if not final_text: final_text = "I've generated this for you:"

            # Final Display
            response_placeholder.markdown(final_text)
            if img_url:
                time.sleep(0.5) # Server sync
                st.image(img_url, use_container_width=True)
            
            # Store data separately
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url})

        except Exception as e:
            st.error(f"Nexus Error: {e}")
            
