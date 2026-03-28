import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import os

# --- 1. NEXUS PREMIUM THEME ---
st.set_page_config(page_title="Nexus Flow Ultra v3.0", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #020617 100%); color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: rgba(15, 23, 42, 0.8); backdrop-filter: blur(10px); border-right: 1px solid rgba(255, 255, 255, 0.1); }
    .stChatMessage { background-color: rgba(30, 41, 59, 0.5) !important; border-radius: 20px !important; border: 1px solid rgba(255, 255, 255, 0.05) !important; padding: 15px !important; margin-bottom: 12px !important; }
    .thinking-box { background: rgba(0, 245, 255, 0.05); border-left: 4px solid #00f5ff; padding: 15px; border-radius: 10px; color: #00f5ff; font-family: monospace; margin: 10px 0; }
    .stButton>button { background: linear-gradient(90deg, #00f5ff, #7000ff); color: white !important; font-weight: 700 !important; border-radius: 12px !important; border: none !important; transition: 0.3s; width: 100%; }
    .stButton>button:hover { box-shadow: 0 0 20px rgba(0, 245, 255, 0.6); transform: translateY(-2px); }
    .nexus-title { font-size: 3.5rem; font-weight: 900; background: linear-gradient(to right, #00f5ff, #7000ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KEYS & INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("⚠️ Keys Missing! Add GROQ_API_KEY and GOOGLE_API_KEY in Secrets.")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# --- 3. CORE FUNCTIONS ---
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

# --- 4. SESSION STATE (Memory) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "db" not in st.session_state:
    st.session_state.db = None
    st.session_state.chunks = None

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:#00f5ff; text-align:center;'>⚡ Nexus Hub</h2>", unsafe_allow_html=True)
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()
    st.markdown("---")
    uploaded = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("🚀 Sync Brain"):
        with st.spinner("Learning..."):
            st.session_state.db, st.session_state.chunks = process_pdfs(uploaded)
            st.success("Synced!")

# --- 6. MAIN CHAT ---
if not st.session_state.messages:
    st.markdown("<div class='nexus-title'>Nexus Flow Ultra</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#94a3b8;'>Advanced Intelligence for Sanjeev</p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎨 Generate MIT Lab Image"):
            st.session_state.messages.append({"role":"user", "content":"Futuristic MIT Lab photo"})
            st.rerun()
    with col2:
        if st.button("🧠 SAT Math Challenge"):
            st.session_state.messages.append({"role":"user", "content":"Give me a tough SAT math logic question"})
            st.rerun()
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m: st.image(m["image"])

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

            sys_msg = f"You are Nexus Flow Ultra. Partner of Sanjeev. Use <thinking> for logic. Use [GENERATE_IMAGE: prompt] for photos. Context: {context}"
            hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-6:]]
            
            # FIXED MODEL NAME HERE
            response = client.chat.completions.create(
                model="llama-3.3-70b-specdec",
                messages=[{"role": "system", "content": sys_msg}] + hist,
                temperature=0.6
            )
            
            raw_res = response.choices[0].message.content
            final_text, img_url = raw_res, None

            if "<thinking>" in raw_res:
                parts = raw_res.split("</thinking>")
                st.markdown(f'<div class="thinking-box"><b>🔍 Reasoning:</b><br>{parts[0].replace("<thinking>","").strip()}</div>', unsafe_allow_html=True)
                final_text = parts[1].strip()

            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    p_str = match.group(1).strip()
                    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p_str)}?width=1024&height=1024&nologo=true"
                    final_text = f"🎨 **Visualizing:** {p_str}"

            st.markdown(final_text)
            if img_url: st.image(img_url)
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url} if img_url else {"role": "assistant", "content": final_text})
        except Exception as e:
            st.error(f"Error: {e}")
            
