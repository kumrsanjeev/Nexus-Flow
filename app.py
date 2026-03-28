import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import os

# --- 1. NEXUS LIGHT THEME (Gemini Style) ---
st.set_page_config(page_title="Nexus Flow Ultra", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f0f2f5; color: #1f1f1f; }
    [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e0e0e0; }
    .stChatMessage {
        background-color: #ffffff !important;
        border-radius: 15px !important;
        border: 1px solid #e0e0e0 !important;
        padding: 15px !important;
        margin-bottom: 12px !important;
        color: #1f1f1f !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .thinking-box {
        background: #f8f9fa;
        border-left: 4px solid #1a73e8;
        padding: 15px;
        border-radius: 8px;
        color: #1a73e8;
        font-family: 'Segoe UI', sans-serif;
        margin: 10px 0;
        font-size: 0.9rem;
    }
    .stButton>button {
        background: #1a73e8 !important;
        color: white !important;
        border-radius: 20px !important;
        border: none !important;
        width: 100%;
    }
    .nexus-title { font-size: 3rem; font-weight: 800; color: #1a73e8; text-align: center; }
    .stChatInput { border-radius: 25px !important; border: 1px solid #ced4da !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KEYS & INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("⚠️ API Keys Missing in Secrets!")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# --- 3. KNOWLEDGE FUNCTIONS ---
def process_pdfs(files):
    text = ""
    for f in files:
        reader = PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
    embeddings = [genai.embed_content(model="models/embedding-001", content=c, task_type="retrieval_document")['embedding'] for c in chunks]
    index = faiss.IndexFlatL2(len(embeddings[0]))
    index.add(np.array(embeddings).astype('float32'))
    return index, chunks

# --- 4. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "db" not in st.session_state:
    st.session_state.db = None
    st.session_state.chunks = None

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:#1a73e8; text-align:center;'>⚡ Nexus Hub</h2>", unsafe_allow_html=True)
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()
    st.markdown("---")
    uploaded = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("🚀 Sync Knowledge"):
        with st.spinner("Processing..."):
            st.session_state.db, st.session_state.chunks = process_pdfs(uploaded)
            st.success("Brain Synced! ✅")

# --- 6. MAIN CHAT INTERFACE ---
if not st.session_state.messages:
    st.markdown("<div class='nexus-title'>Nexus Flow Ultra 🤖</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#5f6368;'>Sanjeev's Personal Intelligence Partner ✨</p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎨 Create Cyberpunk Art"):
            st.session_state.messages.append({"role":"user", "content":"Cyberpunk city illustration banao 🌃"})
            st.rerun()
    with col2:
        if st.button("🧠 Tough Logic Puzzle"):
            st.session_state.messages.append({"role":"user", "content":"Ek tough logic puzzle pucho 🧩"})
            st.rerun()
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m: st.image(m["image"])

# --- 7. CHAT LOGIC ---
if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            context = ""
            if st.session_state.db:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = st.session_state.db.search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([st.session_state.chunks[i] for i in I[0]])

            # Instructions with Emoji mandate
            sys_msg = f"""
            You are Nexus Flow Ultra. Assistant for Sanjeev. 
            - EMOJIS: Always use suitable emojis in every response to look friendly like ChatGPT.
            - LOGIC: Use <thinking> for reasoning.
            - IMAGES: Use [GENERATE_IMAGE: prompt].
            - STYLE: Hinglish.
            - PDF CONTEXT: {context}
            """
            hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-6:]]
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + hist,
                temperature=0.7
            )
            
            raw_res = response.choices[0].message.content
            final_text, img_url = raw_res, None

            # --- SAFE PARSER (Fixes Index Out of Range) ---
            if "<thinking>" in raw_res and "</thinking>" in raw_res:
                parts = raw_res.split("</thinking>")
                thought = parts[0].replace("<thinking>","").strip()
                st.markdown(f'<div class="thinking-box">🔍 <b>Nexus Reasoning:</b><br>{thought}</div>', unsafe_allow_html=True)
                final_text = parts[1].strip()
            elif "<thinking>" in raw_res: # If AI forgot to close tag
                final_text = raw_res.split("<thinking>")[0].strip()
            
            # Image Parser
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    p_str = match.group(1).strip()
                    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p_str)}?width=1024&height=1024&nologo=true"
                    final_text = f"🎨 **Creating Visual:** {p_str}"

            st.markdown(final_text)
            if img_url: st.image(img_url)
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url} if img_url else {"role": "assistant", "content": final_text})
        except Exception as e:
            st.error(f"Nexus Error: {e} ❌")
            
