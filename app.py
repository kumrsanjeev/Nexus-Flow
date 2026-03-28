import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import os

# --- 1. NEXUS PREMIUM CONFIG ---
st.set_page_config(page_title="Nexus Flow Ultra v3.0", page_icon="⚡", layout="wide")

# ChatGPT/Gemini Style CSS
st.markdown("""
    <style>
    .stApp { background: #0E1117; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363d; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #30363d; }
    .thinking-box { background-color: #1a1c23; border-left: 4px solid #00ffcc; padding: 15px; color: #00ffcc; font-family: monospace; border-radius: 8px; margin-bottom: 15px; }
    .stButton>button { width: 100%; border-radius: 8px; background: #21262d; color: white; border: 1px solid #30363d; transition: 0.3s; }
    .stButton>button:hover { border-color: #00ffcc; color: #00ffcc; }
    .main-title { font-size: 3rem; font-weight: 800; background: -webkit-linear-gradient(#00ffcc, #0088ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KEYS & CLIENTS ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("⚠️ Keys Missing! Add GROQ_API_KEY and GOOGLE_API_KEY in Secrets.")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# --- 3. CORE FUNCTIONS (RAG & PDF) ---
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

# --- 4. SESSION STATE (Memory Management) ---
if "messages" not in st.session_state:
    st.session_state.messages = [] # ChatGPT jaisi memory
if "db" not in st.session_state:
    st.session_state.db = None
if "chunks" not in st.session_state:
    st.session_state.chunks = None

# --- 5. SIDEBAR (New Chat & PDF Center) ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>⚡ Nexus Hub</h1>", unsafe_allow_html=True)
    
    # New Chat Button (ChatGPT Jaisa)
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()
    
    st.markdown("---")
    st.subheader("📁 Knowledge Base")
    uploaded_files = st.file_uploader("Upload PDFs for Analysis", type="pdf", accept_multiple_files=True)
    if uploaded_files and st.button("Sync Nexus Brain"):
        with st.spinner("Learning..."):
            st.session_state.db, st.session_state.chunks = process_pdfs(uploaded_files)
            st.success("Synced!")
    
    st.markdown("---")
    st.info("Goal: 1500+ SAT | JEE 2027 | CS Engineer")

# --- 6. MAIN INTERFACE ---
if not st.session_state.messages:
    # Beautiful Home Page
    st.markdown("<div class='main-title'>Nexus Flow Ultra</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8b949e;'>Next-Gen Intelligence for Sanjeev</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("🎨 Generate 3D CS Lab Image", on_click=lambda: st.session_state.messages.append({"role":"user", "content":"Futuristic CS Lab ki photo banao"}))
        st.button("📚 Practice SAT Math Logic", on_click=lambda: st.session_state.messages.append({"role":"user", "content":"SAT Math ka ek tough logic question pucho"}))
    with col2:
        st.button("💻 Help with Python Coding", on_click=lambda: st.session_state.messages.append({"role":"user", "content":"Python data science ke liye basic roadmap batao"}))
        st.button("📝 Summarize my Uploaded PDF", on_click=lambda: st.session_state.messages.append({"role":"user", "content":"Uploaded PDF ko summarize karo"}))
else:
    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "image" in message:
                st.image(message["image"])

# --- 7. INPUT & RESPONSE ---
if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # RAG Context Search
            context = ""
            if st.session_state.db:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = st.session_state.db.search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([st.session_state.chunks[i] for i in I[0]])

            # Build Memory Context for Groq
            history_context = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]] # Last 5 messages for memory
            
            system_prompt = f"""
            You are Nexus Flow Ultra. You are Sanjeev's partner in his goal of 1500+ SAT and CS Engineering.
            - LOGIC: Use <thinking> tags for deep reasoning.
            - IMAGES: Use [GENERATE_IMAGE: prompt] for photos.
            - STYLE: Witty, Professional Hinglish.
            - PDF CONTEXT: {context}
            """
            
            # API Call to Groq (Llama 3 70B)
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "system", "content": system_prompt}] + history_context,
                temperature=0.7
            )
            
            full_res = response.choices[0].message.content
            
            # Parsing Logic
            final_text = full_res
            img_url = None

            if "<thinking>" in full_res:
                parts = full_res.split("</thinking>")
                st.markdown(f'<div class="thinking-box">🧠 <b>Thinking:</b><br>{parts[0].replace("<thinking>","").strip()}</div>', unsafe_allow_html=True)
                final_text = parts[1].strip()

            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(img_prompt)}?width=1024&height=1024&nologo=true"
                    final_text = f"🎨 **Visualizing:** {img_prompt}"

            st.markdown(final_text)
            if img_url:
                st.image(img_url)
            
            # Save to Memory
            msg_data = {"role": "assistant", "content": final_text}
            if img_url: msg_data["image"] = img_url
            st.session_state.messages.append(msg_data)

        except Exception as e:
            st.error(f"Nexus Error: {str(e)}")
            
