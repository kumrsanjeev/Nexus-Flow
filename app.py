import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import os

# --- 1. NEXUS PREMIUM THEME (Glassmorphism & Neon) ---
st.set_page_config(page_title="Nexus Flow Ultra", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    /* Global Background */
    .stApp {
        background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617);
        color: #f8fafc;
    }

    /* Sidebar Glass Effect */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.7) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(0, 245, 255, 0.1);
    }

    /* Chat Bubbles like Gemini */
    .stChatMessage {
        background: rgba(30, 41, 59, 0.4) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        margin-bottom: 15px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }

    /* Thinking Logic Box */
    .thinking-box {
        background: rgba(0, 245, 255, 0.03);
        border-left: 3px solid #00f5ff;
        padding: 15px;
        border-radius: 12px;
        color: #00f5ff;
        font-family: 'Fira Code', monospace;
        font-size: 0.85rem;
        margin: 10px 0;
    }

    /* Neon Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #00f5ff, #7000ff) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1rem !important;
        transition: 0.4s ease-in-out !important;
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px rgba(0, 245, 255, 0.5);
        transform: scale(1.02);
    }

    /* Input Box Styling */
    .stChatInputContainer {
        padding-bottom: 2rem;
    }
    .stChatInput {
        border-radius: 30px !important;
        border: 1px solid rgba(0, 245, 255, 0.2) !important;
        background: #1e293b !important;
    }

    /* Gradient Title */
    .nexus-title {
        font-size: 3.8rem;
        font-weight: 900;
        background: linear-gradient(to right, #00f5ff, #bfdbfe, #7000ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-top: -20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KEYS & INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("⚠️ API Keys Missing! Please add them in Secrets.")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# --- 3. KNOWLEDGE FUNCTIONS (PDF) ---
def process_knowledge(files):
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
if "chunks" not in st.session_state:
    st.session_state.chunks = None

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:#00f5ff; text-align:center;'>⚡ Nexus Hub</h2>", unsafe_allow_html=True)
    if st.button("➕ New Conversation"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()
    
    st.markdown("---")
    st.write("📂 **Knowledge Base**")
    uploaded = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("🚀 Sync Brain"):
        with st.spinner("Absorbing..."):
            st.session_state.db, st.session_state.chunks = process_knowledge(uploaded)
            st.success("Brain Updated!")
    
    st.markdown("---")
    st.caption("Sanjeev's AI Collaborator | v3.0 Ultra")

# --- 6. MAIN CHAT INTERFACE ---
if not st.session_state.messages:
    st.markdown("<div class='nexus-title'>Nexus Flow Ultra</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#94a3b8;'>Advanced Intelligence for Sanjeev</p>", unsafe_allow_html=True)
    
    # Home Page Suggestions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎨 Create Cyberpunk MIT Lab"):
            st.session_state.messages.append({"role":"user", "content":"Futuristic MIT Lab ki photo banao neon style mein"})
            st.rerun()
    with col2:
        if st.button("🧠 Tough SAT Math Challenge"):
            st.session_state.messages.append({"role":"user", "content":"SAT Math logic ka ek tough question pucho aur thinking mode use karo"})
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
            # Context Search
            context = ""
            if st.session_state.db:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = st.session_state.db.search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([st.session_state.chunks[i] for i in I[0]])

            # Prompt Engineering
            sys_msg = f"You are Nexus Flow Ultra. Partner of Sanjeev. Goals: 1500+ SAT, CS Engineer. Use <thinking> for logic. Use [GENERATE_IMAGE: prompt] for photos. Style: Professional Hinglish. PDF Context: {context}"
            
            # History Memory (Last 6 messages)
            hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-6:]]
            
            # Groq Llama-3 Call
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "system", "content": sys_msg}] + hist,
                temperature=0.6
            )
            
            raw_res = response.choices[0].message.content
            final_text, img_url = raw_res, None

            # Thinking Parser
            if "<thinking>" in raw_res:
                parts = raw_res.split("</thinking>")
                st.markdown(f'<div class="thinking-box"><b>🔍 Nexus Reasoning:</b><br>{parts[0].replace("<thinking>","").strip()}</div>', unsafe_allow_html=True)
                final_text = parts[1].strip()

            # Image Parser
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    p_str = match.group(1).strip()
                    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p_str)}?width=1024&height=1024&nologo=true"
                    final_text = f"🎨 **Generated:** {p_str}"

            st.markdown(final_text)
            if img_url: st.image(img_url)
            
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url} if img_url else {"role": "assistant", "content": final_text})

        except Exception as e:
            st.error(f"Nexus Sync Error: {e}")
            
