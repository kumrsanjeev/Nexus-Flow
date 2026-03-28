import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import random

# --- 1. PREMIUM LIGHT THEME (Gemini/ChatGPT Style) ---
st.set_page_config(page_title="Nexus Flow Ultra", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #37352f; }
    [data-testid="stSidebar"] { background-color: #f7f7f8 !important; border-right: 1px solid #d1d5db; }
    .stChatMessage { border-radius: 12px; padding: 1.2rem !important; margin-bottom: 1rem; border: 1px solid #f0f0f0 !important; }
    .stChatInputContainer { padding-bottom: 2rem; }
    .stChatInput { border-radius: 26px !important; border: 1px solid #e5e7eb !important; }
    .main-header { font-size: 2.5rem; font-weight: 600; text-align: center; margin-bottom: 2rem; color: #1f2937; }
    /* Pill Buttons */
    .stButton>button {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 20px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
    }
    .stButton>button:hover { border-color: #1a73e8 !important; color: #1a73e8 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KEYS & INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("Secrets missing! Please add GROQ_API_KEY and GOOGLE_API_KEY.")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

if "messages" not in st.session_state: st.session_state.messages = []
if "db" not in st.session_state: st.session_state.db = None

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='text-align:center;'>Nexus Hub ⚡</h3>", unsafe_allow_html=True)
    if st.button("➕ New Conversation"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()
    st.markdown("---")
    uploaded = st.file_uploader("Upload PDFs 📂", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("🚀 Sync Brain"):
        text = ""
        for f in uploaded:
            reader = PdfReader(f)
            for page in reader.pages: text += page.extract_text() or ""
        chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
        embeddings = [genai.embed_content(model="models/embedding-001", content=c, task_type="retrieval_document")['embedding'] for c in chunks]
        index = faiss.IndexFlatL2(len(embeddings[0]))
        index.add(np.array(embeddings).astype('float32'))
        st.session_state.db, st.session_state.chunks = index, chunks
        st.success("Brain Synced! ✅")

# --- 4. HOME PAGE (Gemini Style) ---
if not st.session_state.messages:
    st.markdown("<div class='main-header'>What can I help with, Sanjeev? ✨</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🖼️ Create image of a dog 🐕"):
            st.session_state.messages.append({"role":"user", "content":"Ek pyare kutte ki photo banao 🐶"})
            st.rerun()
    with col2:
        if st.button("📝 SAT Practice Question 🧠"):
            st.session_state.messages.append({"role":"user", "content":"Give me a tough SAT math question"})
            st.rerun()
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m and m["image"]:
                st.image(m["image"], use_container_width=True)

# --- 5. CHAT LOGIC (Language & Visual Fix) ---
if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # Context search
            context = ""
            if st.session_state.db:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = st.session_state.db.search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([st.session_state.chunks[idx] for idx in I[0]])

            # MANDATORY RULES
            sys_msg = f"""
            You are Nexus Flow Ultra.
            - LANGUAGE: Reply in the EXACT same language/style as the user (Hindi/English/Hinglish).
            - EMOJIS: Use suitable emojis in every sentence to be friendly like ChatGPT/Gemini 🚀✨.
            - IMAGE: If user asks for an image, respond ONLY with: [GENERATE_IMAGE: highly descriptive English prompt]. Never say "I can't generate images".
            - FORMATTING: Use bold text and bullet points for long answers.
            Context: {context}
            """
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-6:]],
                stream=True
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
            # --- IMAGE GENERATION FIX ---
            img_url = None
            if "[GENERATE_IMAGE:" in full_response:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', full_response)
                if match:
                    img_prompt = match.group(1).strip()
                    # Fix: Encoding URL properly and adding random seed
                    encoded_prompt = urllib.parse.quote(img_prompt)
                    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={random.randint(0, 99999)}"
                    st.image(img_url, use_container_width=True)

            st.session_state.messages.append({"role": "assistant", "content": full_response, "image": img_url})

        except Exception as e:
            st.error(f"Error: {e} ❌")
        
