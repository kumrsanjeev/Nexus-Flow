import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import random
import time

# --- 1. PREMIUM GEMINI UI THEME ---
st.set_page_config(page_title="Nexus Flow Ultra v18", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    /* Gemini White Theme */
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #f0f4f9 !important; border-right: none; }

    /* Gemini style message bubbles */
    .stChatMessage { background-color: transparent !important; border: none !important; padding: 10px 0 !important; }
    
    /* Suggested Buttons (Pills) */
    .stButton>button {
        background-color: #ffffff !important;
        color: #444746 !important;
        border: 1px solid #c4c7c5 !important;
        border-radius: 25px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        text-align: left !important;
        display: block;
        margin-bottom: 10px;
        transition: 0.3s;
        width: 100%;
    }
    .stButton>button:hover { background-color: #f1f3f4 !important; border-color: #1a73e8 !important; }

    /* Thinking box (Logic) */
    .thinking-box {
        background-color: #f0f7ff;
        border-radius: 12px;
        padding: 15px;
        color: #0056b3;
        font-size: 0.9rem;
        border-left: 5px solid #0056b3;
        margin: 10px 0;
        font-family: 'Courier New', monospace;
    }

    /* Gemini Title Style */
    .gemini-greeting { font-size: 3rem; font-weight: 500; color: #1f1f1f; margin-top: 80px; }
    .gemini-subtitle { font-size: 2.8rem; font-weight: 500; color: #c4c7c5; margin-bottom: 50px; }

    /* Chat Input Styling */
    .stChatInputContainer { padding-bottom: 30px; }
    .stChatInput { border-radius: 30px !important; background-color: #f0f4f9 !important; border: none !important; }
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
    st.markdown("<h3 style='color:#1a73e8; text-align:center;'>Nexus Core ⚡</h3>", unsafe_allow_html=True)
    if st.button("➕ New Deep Chat"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()
    st.markdown("---")
    uploaded = st.file_uploader("Upload PDFs for Analysis", type="pdf", accept_multiple_files=True)
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
        st.success("Docs Synced! ✅")

# --- 4. GEMINI HOME PAGE (Is Back!) ---
if not st.session_state.messages:
    st.markdown("<div class='gemini-greeting'>Hi Sanjeev</div>", unsafe_allow_html=True)
    st.markdown("<div class='gemini-subtitle'>Where should we start?</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🖼️ **Create Image:** Futurist computer lab with 3D holograms"):
            st.session_state.messages.append({"role":"user", "content":"Futurist computer lab with 3D holograms"})
            st.rerun()
        if st.button("📝 **Write:** Hinglish essay on AI's impact on India"):
            st.session_state.messages.append({"role":"user", "content":"Hinglish essay on AI's impact on India"})
            st.rerun()
    with col2:
        if st.button("💻 **Code:** Python script to analyze PDF documents"):
            st.session_state.messages.append({"role":"user", "content":"Python script to analyze PDF documents"})
            st.rerun()
        if st.button("🧠 **Logic:** Refraction of light deep Hinglish explanation"):
            st.session_state.messages.append({"role":"user", "content":"Refraction of light deep Hinglish explanation"})
            st.rerun()
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m and m["image"]:
                st.image(m["image"], use_container_width=True)

# --- 5. CHAT ENGINE (Super Logic Mode) ---
if prompt := st.chat_input("Message Nexus..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # RAG Context retrieval
            context = ""
            if st.session_state.db:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = st.session_state.db.search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([st.session_state.chunks[idx] for idx in I[0]])

            # MANDATORY GEMINI PERSONA SYSTEM PROMPT
            sys_msg = f"""You are Nexus Flow Ultra in 'Gemini' Mode.
            - PERSONA: Be friendly, extremamente inteligente, and professional. Mirror Hinglish.
            - FORMATTING: Answer like Gemini. Use bold headings, bullet points, and code blocks.
            - IMAGES: Use [GENERATE_IMAGE: descriptive English prompt] for photos. Never show tag to user.
            - DEEP LOGIC: For difficult logic, use <thinking> detailed step-by-step logic </thinking> first. Context: {context}"""
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-8:]],
                stream=True,
                temperature=0.6 # Logic ke liye balance temperature
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            # --- PARSING & VISUAL ENGINE ---
            final_text = full_response
            img_url = None

            # 1. Super Logic Box
            if "<thinking>" in full_response:
                parts = full_response.split("</thinking>")
                thought = parts[0].replace("<thinking>","").strip()
                st.markdown(f'<div class="thinking-box">🔍 <b>Super Thinking:</b><br>{thought}</div>', unsafe_allow_html=True)
                final_text = parts[-1].strip()

            # 2. IMAGE ENGINE (Stable Seed Fix)
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    encoded_p = urllib.parse.quote(img_prompt)
                    # Correct URL with stable random seed
                    img_url = f"https://image.pollinations.ai/prompt/{encoded_p}?width=1024&height=1024&nologo=true&seed={np.random.randint(0, 99999)}"
                    final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()
                    if not final_text: final_text = f"🎨 **Creating Image:** {img_prompt}"

            response_placeholder.markdown(final_text)
            if img_url: 
                st.image(img_url, use_container_width=True)
            
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url})

        except Exception as e:
            st.error(f"Nexus Sync Error: {e}")
                                              
