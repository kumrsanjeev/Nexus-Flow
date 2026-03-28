import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import random

# --- 1. PREMIUM GEMINI UI THEME ---
st.set_page_config(page_title="Nexus Flow Ultra v12", page_icon="🧠", layout="wide")

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
    }
    .stChatInput { border-radius: 30px !important; background-color: #f0f4f9 !important; border: 1px solid #e0e0e0 !important; }
    .nexus-title { font-size: 2.8rem; font-weight: 600; text-align: center; color: #1a73e8; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KEYS & INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("Missing API Keys in Streamlit Secrets!")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

if "messages" not in st.session_state: st.session_state.messages = []
if "db" not in st.session_state: st.session_state.db = None

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='text-align:center;'>Nexus Core ⚡</h3>", unsafe_allow_html=True)
    if st.button("➕ New Chat Session"):
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
            if "image" in m and m["image"]: st.image(m["image"], use_container_width=True)

# --- 5. CORE LOGIC ---
if prompt := st.chat_input("Ask a deep question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            context = ""
            if st.session_state.db:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = st.session_state.db.search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([st.session_state.chunks[idx] for idx in I[0]])

            sys_msg = f"""You are Nexus Flow Ultra.
            1. LANGUAGE: Reply in the EXACT same language as the user.
            2. FORMATTING: Use bold headings and bullet points like ChatGPT.
            3. EMOJIS: Always use suitable emojis. 🚀✨
            4. IMAGES: If asked for an image, use ONLY this format: [GENERATE_IMAGE: English prompt].
            Context: {context}"""
            
            # STABLE MODEL: llama-3.3-70b-versatile
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-8:]],
                stream=True,
                temperature=0.6
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
            # PARSING IMAGE
            img_url = None
            if "[GENERATE_IMAGE:" in full_response:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', full_response)
                if match:
                    img_prompt = match.group(1).strip()
                    encoded_prompt = urllib.parse.quote(img_prompt)
                    # FIX: Added required b argument (0, 99999) to randint
                    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={random.randint(0, 99999)}"
                    st.image(img_url, use_container_width=True)

            st.session_state.messages.append({"role": "assistant", "content": full_response, "image": img_url})

        except Exception as e:
            st.error(f"Nexus Error: {e} ❌")
            
