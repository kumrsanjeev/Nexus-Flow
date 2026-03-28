import streamlit as st
import google.generativeai as genai
from groq import Groq
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import os
import random

# --- 1. CONFIG & THEME SETUP (merged agent style) ---
st.set_page_config(page_title="Nexus Flow Pro 🤖", layout="wide", page_icon="⚡")

# Gemini style light theme with blue accents
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f5; color: #111111; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e0e0e0; }
    .stChatMessage { border-radius: 15px; border: 1px solid #e0e0e0 !important; background-color: #ffffff !important; margin-bottom: 12px; color: #111111 !important; }
    .stChatMessage.stChatMessage--user { background-color: rgba(26, 115, 232, 0.05) !important; }
    .stButton>button { background: #1a73e8; color: white; border-radius: 20px; border: none; width: 100%; transition: 0.2s; }
    .stButton>button:hover { background: #1765cc; box-shadow: 0 4px 10px rgba(26, 115, 232, 0.3); }
    .nexus-title { font-size: 3rem; font-weight: 800; color: #1a73e8; text-align: center; }
    .stChatInput { border-radius: 25px !important; border: 1px solid #ced4da !important; }
    .thinking-box { background: rgba(26, 115, 232, 0.03); border-left: 4px solid #1a73e8; padding: 15px; border-radius: 8px; color: #1a73e8; font-family: sans-serif; margin: 10px 0; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KEYS & CLIENTS (merged agent core) ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("⚠️ API Keys Missing! Add GROQ_API_KEY and GOOGLE_API_KEY in Streamlit Secrets.")
    st.stop()

groq_client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# --- 3. KNOWLEDGE BASE CORE (merged agent functions) ---
def get_embeddings_from_pdf(pdf_files):
    text = ""
    for f in pdf_files:
        reader = PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    
    # Simple chunking (agent logic)
    chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
    embeddings = [genai.embed_content(model="models/embedding-001", content=c, task_type="retrieval_document")['embedding'] for c in chunks]
    
    index = faiss.IndexFlatL2(len(embeddings[0]))
    index.add(np.array(embeddings).astype('float32'))
    return index, chunks

# --- 4. SESSION STATE (Memory) ---
if "messages" not in st.session_state: st.session_state.messages = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
    st.session_state.chunks = None

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("⚡ Nexus Hub")
    if st.button("➕ New Conversation"):
        st.session_state.messages = []
        st.session_state.vector_store = None
        st.rerun()
    st.markdown("---")
    st.write("📂 **Knowledge Base**")
    uploaded_files = st.file_uploader("Upload PDFs for context", type="pdf", accept_multiple_files=True)
    if uploaded_files and st.button("Sync Nexus Brain"):
        with st.spinner("Learning..."):
            st.session_state.vector_store, st.session_state.chunks = get_embeddings_from_pdf(uploaded_files)
            st.success("Docs synced!")

# --- 6. MAIN CHAT INTERFACE ---
if not st.session_state.messages:
    # Home Page suggestions
    st.markdown("<div class='nexus-title'>Nexus Flow Pro</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#5f6368;'>Personal AI Partner for Sanjeev</p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎨 Create Cyberpunk MIT Lab"):
            st.session_state.messages.append({"role":"user", "content":"Cyberpunk city illustration involving MIT lab"})
            st.rerun()
    with col2:
        if st.button("🧠 Tough SAT Math Challenge"):
            st.session_state.messages.append({"role":"user", "content":"Give me a tough SAT math logic question"})
            st.rerun()
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m: st.image(m
                                      
