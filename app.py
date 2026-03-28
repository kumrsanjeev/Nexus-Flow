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

# --- 1. PREMIUM GEMINI INTERFACE ---
st.set_page_config(page_title="Nexus Flow Ultra v10", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    [data-testid="stSidebar"] { background-color: #f0f4f9 !important; border-right: none; }
    .stChatMessage { border-radius: 12px; padding: 15px !important; margin-bottom: 12px; border: 1px solid #f0f2f6 !important; }
    .thinking-box { 
        background-color: #f8f9ff; 
        border-radius: 12px; 
        padding: 15px; 
        color: #1a73e8; 
        border-left: 5px solid #1a73e8; 
        margin-bottom: 15px; 
        font-size: 0.95rem;
        font-family: 'Segoe UI', sans-serif;
    }
    .stChatInput { border-radius: 30px !important; background-color: #f0f4f9 !important; border: 1px solid #e0e0e0 !important; }
    .nexus-title { font-size: 2.8rem; font-weight: 600; text-align: center; color: #1a73e8; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KEYS & INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

if "messages" not in st.session_state: st.session_state.messages = []
if "db" not in st.session_state: st.session_state.db = None

# --- 3. SIDEBAR (History & PDFs) ---
with st.sidebar:
    st.markdown("<h3 style='text-align:center;'>Nexus Core ⚡</h3>", unsafe_allow_html=True)
    if st.button("➕ New Deep Chat"):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    uploaded = st.file_uploader("Upload PDFs for Deep Analysis", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("🚀 Sync Knowledge"):
        with st.spinner("Processing..."):
            text = ""
            for f in uploaded:
                reader = PdfReader(f)
                for page in reader.pages: text += page.extract_text() or ""
            chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
            embeddings = [genai.embed_content(model="models/embedding-001", content=c, task_type="retrieval_document")['embedding'] for c in chunks]
            index = faiss.IndexFlatL2(len(embeddings[0]))
            index.add(np.array(embeddings).astype('float32'))
            st.session_state.db, st.session_state.chunks = index, chunks
            st.success("Deep Knowledge Synced!")

# --- 4. MAIN INTERFACE ---
if not st.session_state.messages:
    st.markdown("<div class='nexus-title'>Nexus Flow Ultra 🧠</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#5f6368;'>Powered by LLaMA 3.3 for Deep Reasoning</p>", unsafe_allow_html=True)
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m and m["image"]: st.image(m["image"])

# --- 5. DEEP LOGIC ENGINE ---
if prompt := st.chat_input("Ask a deep question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

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

            # DEEP ANSWER SYSTEM PROMPT
            sys_msg = f"""
            You are Nexus Flow Ultra (Deep Thinking Mode). 
            - LOGIC: You MUST use <thinking> tags to break down complex problems step-by-step before answering.
            - DEPTH: Provide detailed, comprehensive, and logically sound answers.
            - LANGUAGE: Reply in the user's language (Hindi/Japanese/Hinglish).
            - IMAGES: Use [GENERATE_IMAGE: prompt] if visual aid is needed.
            Context: {context}
            """
            
            # Using LLaMA 3.3-70b (The Reasoning King)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-specdec",
                messages=[{"role": "system", "content": sys_msg}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-8:]],
                stream=True,
                temperature=0.5 # Low temperature for more logical/deep answers
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            # --- PARSING ---
            final_text = full_response
            img_url = None

            if "<thinking>" in full_response and "</thinking>" in full_response:
                parts = full_response.split("</thinking>")
                thought = parts[0].replace("<thinking>","").strip()
                st.markdown(f'<div class="thinking-box"><b>🔍 Deep Logic:</b><br>{thought}</div>', unsafe_allow_html=True)
                final_text = parts[1].strip()

            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    encoded_p = urllib.parse.quote(img_prompt)
                    img_url = f"https://image.pollinations.ai/prompt/{encoded_p}?width=1024&height=1024&nologo=true&seed={random.randint(0, 99999)}"
                    final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()

            response_placeholder.markdown(final_text)
            if img_url: st.image(img_url, use_container_width=True)
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url})

        except Exception as e:
            st.error(f"Sync Error: {e}")
            
