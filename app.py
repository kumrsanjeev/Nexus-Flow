import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import os
import random

# --- 1. CLEAN GEMINI INTERFACE ---
st.set_page_config(page_title="Nexus Flow Ultra", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    [data-testid="stSidebar"] { background-color: #f0f4f9 !important; border-right: none; }
    .stChatMessage { background-color: transparent !important; border: none !important; padding: 10px 0 !important; }
    .stButton>button {
        background-color: #ffffff !important;
        color: #444746 !important;
        border: 1px solid #c4c7c5 !important;
        border-radius: 25px !important;
        padding: 8px 20px !important;
        font-weight: 500 !important;
    }
    .stChatInput { border-radius: 30px !important; background-color: #f0f4f9 !important; border: none !important; }
    .thinking-box { background-color: #f1f3f4; border-radius: 12px; padding: 15px; color: #1a73e8; border-left: 5px solid #1a73e8; margin-bottom: 10px; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API KEYS & INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("API Keys missing in Secrets!")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# --- 3. PERSISTENT MEMORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "db" not in st.session_state:
    st.session_state.db = None

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:#1a73e8; text-align:center;'>Nexus Hub ⚡</h3>", unsafe_allow_html=True)
    if st.button("➕ Start New Chat"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()
    
    st.markdown("---")
    uploaded = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("🚀 Sync Knowledge"):
        text = ""
        for f in uploaded:
            reader = PdfReader(f)
            for page in reader.pages: text += page.extract_text() or ""
        chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
        embeddings = [genai.embed_content(model="models/embedding-001", content=c, task_type="retrieval_document")['embedding'] for c in chunks]
        index = faiss.IndexFlatL2(len(embeddings[0]))
        index.add(np.array(embeddings).astype('float32'))
        st.session_state.db, st.session_state.chunks = index, chunks
        st.success("Brain Synced!")

# --- 5. CHAT DISPLAY ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m and m["image"]:
            st.image(m["image"], use_container_width=True)

# --- 6. CORE CHAT LOGIC (Strict Language Mirroring) ---
if prompt := st.chat_input("Ask Gemini..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # Context retrieval
            context = ""
            if st.session_state.db:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = st.session_state.db.search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([st.session_state.chunks[idx] for idx in I[0]])

            # MANDATORY LANGUAGE LOCK RULES
            sys_msg = f"""
            You are Nexus Flow Ultra. 
            - LANGUAGE RULE: You MUST detect the language of the user's input and reply ONLY in that language. 
              (If user says "Hi" after a Japanese chat, reply in Japanese: "こんにちは！").
            - MEMORY: Remember previous conversation details.
            - IMAGES: Use [GENERATE_IMAGE: descriptive English prompt] for photos.
            - EMOJIS: Use relevant emojis.
            Context: {context}
            """
            
            chat_hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-10:]]
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + chat_hist,
                stream=True
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            # --- IMAGE & LOGIC PARSER ---
            final_text = full_response
            img_url = None

            # Hide Generate Tag from User
            if "[GENERATE_IMAGE:" in full_response:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', full_response)
                if match:
                    img_prompt = match.group(1).strip()
                    encoded_p = urllib.parse.quote(img_prompt)
                    img_url = f"https://image.pollinations.ai/prompt/{encoded_p}?width=1024&height=1024&nologo=true&seed={random.randint(0, 99999)}"
                    final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', full_response).strip()

            response_placeholder.markdown(final_text)
            if img_url:
                st.image(img_url, use_container_width=True)

            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url})

        except Exception as e:
            st.error(f"Error: {e}")
