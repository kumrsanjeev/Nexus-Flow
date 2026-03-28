import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import os

# --- 1. NEXUS GEMINI THEME & CONFIG ---
st.set_page_config(page_title="Nexus Flow Ultra", page_icon="⚡", layout="wide")

# Gemini White/Light Theme Styling
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; color: #1f1f1f; }
    [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e0e0e0; }
    .stChatMessage { border-radius: 12px; border: 1px solid #e0e0e0 !important; background-color: #ffffff !important; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .nexus-title { font-size: 2.5rem; font-weight: 700; color: #1a73e8; text-align: center; margin-top: -30px; }
    .stButton>button { border-radius: 20px !important; background: #1a73e8 !important; color: white !important; font-weight: 600; width: 100%; }
    .stChatInputContainer { padding-bottom: 20px; }
    .thinking-box { background: #f1f3f4; border-left: 4px solid #1a73e8; padding: 12px; border-radius: 8px; color: #1a73e8; font-size: 0.85rem; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIN SYSTEM ---
def login():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.markdown("<h1 style='text-align:center;'>🔐 Nexus Login</h1>", unsafe_allow_html=True)
        with st.container():
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                user = st.text_input("Username")
                pw = st.text_input("Password", type="password")
                if st.button("Login"):
                    if user == "Sanjeev" and pw == "nexus123":
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password")
        st.stop()

login() # Trigger Login

# --- 3. INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("Missing API Keys in Secrets!")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# --- 4. ENGINE FUNCTIONS ---
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

# --- 5. SESSION STATE (Chat History & Memory) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "db" not in st.session_state:
    st.session_state.db = None
    st.session_state.chunks = None

# --- 6. SIDEBAR (Chat History Management) ---
with st.sidebar:
    st.markdown("<h2 style='color:#1a73e8;'>⚡ Nexus Hub</h2>", unsafe_allow_html=True)
    st.write(f"Logged in as: **Sanjeev**")
    
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()
    
    st.markdown("---")
    st.subheader("📚 Chat Memory")
    if not st.session_state.messages:
        st.caption("No history yet.")
    else:
        for i, msg in enumerate(st.session_state.messages[:5]):
            if msg["role"] == "user":
                st.caption(f"💬 {msg['content'][:25]}...")

    st.markdown("---")
    uploaded = st.file_uploader("Upload PDF Knowledge", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("Sync Brain"):
        with st.spinner("Processing..."):
            st.session_state.db, st.session_state.chunks = process_pdfs(uploaded)
            st.success("Synced! ✅")

# --- 7. MAIN CHAT INTERFACE ---
if not st.session_state.messages:
    st.markdown("<div class='nexus-title'>Hello, Sanjeev</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#5f6368;'>How can I help you today?</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎨 Create a space exploration image"):
            st.session_state.messages.append({"role":"user", "content":"Space exploration ki ek realistic photo banao 🚀"})
            st.rerun()
    with col2:
        if st.button("🧠 Solve a tough coding problem"):
            st.session_state.messages.append({"role":"user", "content":"Python mein ek advanced recursion logic samjhao 💻"})
            st.rerun()
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m:
                st.image(m["image"], use_container_width=True)

# --- 8. CHAT LOGIC ---
if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Context Search
            context = ""
            if st.session_state.db:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = st.session_state.db.search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([st.session_state.chunks[idx] for idx in I[0]])

            sys_msg = f"You are Nexus Flow Ultra. Use Hinglish. Use <thinking> for logic. Use [GENERATE_IMAGE: prompt] for photos. Context: {context}"
            hist = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-10:]]
            
            # Using Llama 3.3 for best logic
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + hist,
                temperature=0.7
            )
            
            raw_res = response.choices[0].message.content
            final_text, img_url = raw_res, None

            # Thinking Parser
            if "<thinking>" in raw_res:
                parts = raw_res.split("</thinking>")
                st.markdown(f'<div class="thinking-box">🔍 <b>Thinking Process:</b><br>{parts[0].replace("<thinking>","").strip()}</div>', unsafe_allow_html=True)
                final_text = parts[1].strip()

            # Image Parser (Direct Show Fix)
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    p_str = match.group(1).strip()
                    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p_str)}?width=1024&height=1024&nologo=true"
                    final_text = f"🎨 **Result for:** {p_str}"

            st.markdown(final_text)
            if img_url:
                st.image(img_url, caption=f"Generated by Nexus for Sanjeev", use_container_width=True)
            
            # Save to history
            msg_data = {"role": "assistant", "content": final_text}
            if img_url: msg_data["image"] = img_url
            st.session_state.messages.append(msg_data)

        except Exception as e:
            st.error(f"Nexus Error: {e} ❌")
    
