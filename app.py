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

# --- 1. GEMINI PREMIUM UI ---
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

# --- 2. KEYS & INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("API Keys missing in Secrets!")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# --- 3. MEMORY & SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [] # Ye hai memory power
if "db" not in st.session_state:
    st.session_state.db = None

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:#1a73e8; text-align:center;'>Nexus Hub ⚡</h3>", unsafe_allow_html=True)
    if st.button("➕ New Chat (Clear Memory)"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()
    
    st.markdown("---")
    st.write("📂 **Knowledge Base**")
    uploaded = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
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
        st.success("Brain Synced!")

# --- 5. CHAT DISPLAY ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m and m["image"]:
            st.image(m["image"], use_container_width=True)

# --- 6. CHAT LOGIC ---
if prompt := st.chat_input("Ask Gemini..."):
    # User message save karna (Memory)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

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

            # Instructions with Memory & Emojis
            sys_msg = f"""
            You are Nexus Flow Ultra. 
            - MEMORY: You MUST remember previous parts of this conversation.
            - LANGUAGE: Reply strictly in the language of the user (Japanese/Hindi/Hinglish).
            - EMOJIS: Always use suitable emojis. 
            - IMAGES: Use [GENERATE_IMAGE: descriptive prompt in English] for visuals.
            Context: {context}
            """
            
            # Memory injection (Last 10 messages)
            chat_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-10:]]
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + chat_history,
                stream=True
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            # --- PARSING & FIXING ---
            final_text = full_response
            img_url = None

            if "<thinking>" in full_response:
                parts = full_response.split("</thinking>")
                st.markdown(f'<div class="thinking-box">🔍 <b>Reasoning:</b><br>{parts[0].replace("<thinking>","").strip()}</div>', unsafe_allow_html=True)
                final_text = parts[1].strip()

            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    encoded_p = urllib.parse.quote(img_prompt)
                    # FIXED Syntax Error below:
                    img_url = f"https://image.pollinations.ai/prompt/{encoded_p}?width=1024&height=1024&nologo=true&seed={random.randint(0, 99999)}"
                    final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()

            response_placeholder.markdown(final_text)
            if img_url:
                st.image(img_url, use_container_width=True)

            # Assistant message save karna (Memory)
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url})

        except Exception as e:
            st.error(f"Error: {e}")
                
