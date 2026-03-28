import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import os

# --- 1. GEMINI LIGHT THEME CONFIG ---
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
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #f1f3f4 !important; border-color: #1a73e8 !important; }

    .thinking-box { 
        background-color: #f0f4f9; 
        border-radius: 12px; 
        padding: 15px; 
        color: #0b57d0; 
        border-left: 4px solid #0b57d0; 
        margin: 10px 0; 
        font-size: 0.9rem; 
    }
    .gemini-greeting { font-size: 2.8rem; font-weight: 500; color: #1f1f1f; margin-top: 50px; }
    .gemini-subtitle { font-size: 2.5rem; font-weight: 500; color: #c4c7c5; margin-bottom: 30px; }
    .stChatInput { border-radius: 30px !important; background-color: #f0f4f9 !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("API Keys missing in Secrets!")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

if "messages" not in st.session_state: st.session_state.messages = []
if "db" not in st.session_state: st.session_state.db = None

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:#1a73e8;'>Nexus Menu</h3>", unsafe_allow_html=True)
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()
    st.markdown("---")
    uploaded = st.file_uploader("Upload Study PDFs", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("Sync Brain"):
        text = ""
        for f in uploaded:
            reader = PdfReader(f)
            for page in reader.pages: text += page.extract_text() or ""
        chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
        embeddings = [genai.embed_content(model="models/embedding-001", content=c, task_type="retrieval_document")['embedding'] for c in chunks]
        index = faiss.IndexFlatL2(len(embeddings[0]))
        index.add(np.array(embeddings).astype('float32'))
        st.session_state.db, st.session_state.chunks = index, chunks
        st.success("Synced! ✅")

# --- 4. HOME PAGE ---
if not st.session_state.messages:
    st.markdown("<div class='gemini-greeting'>Hi Sanjeev</div>", unsafe_allow_html=True)
    st.markdown("<div class='gemini-subtitle'>Where should we start?</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🖼️ Create an image of an AI"):
            st.session_state.messages.append({"role":"user", "content":"Create a high-quality image of a futuristic AI robot 🤖"})
            st.rerun()
    with col2:
        if st.button("📝 SAT Logic Challenge"):
            st.session_state.messages.append({"role":"user", "content":"Ask me a tough SAT math logic question 📝"})
            st.rerun()
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m and m["image"]:
                st.image(m["image"], use_container_width=True)

# --- 5. CHAT LOGIC ---
if prompt := st.chat_input("Ask Gemini"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            context = ""
            if st.session_state.db:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = st.session_state.db.search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([st.session_state.chunks[idx] for idx in I[0]])

            sys_msg = f"""You are Nexus Flow Ultra (Gemini Clone). 
            - IDENTITY: You are Sanjeev's AI partner. 
            - LANGUAGE: Always reply in the user's language (Hindi/Hinglish/English).
            - IMAGE: ONLY use [GENERATE_IMAGE: descriptive prompt in English] if the user EXPLICITLY asks to 'create', 'generate', or 'draw' an image. Do NOT use it for normal questions like 'Who is PM'.
            - PM of INDIA: If asked, say Narendra Modi directly.
            - LOGIC: Use <thinking> for reasoning.
            Context: {context}"""
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-6:]]
            )
            
            raw_res = response.choices[0].message.content
            final_text, img_url = raw_res, None

            # Robust Safe Parser
            if "<thinking>" in raw_res and "</thinking>" in raw_res:
                parts = raw_res.split("</thinking>")
                thought = parts[0].replace("<thinking>","").strip()
                st.markdown(f'<div class="thinking-box">🔍 <b>Thinking Process:</b><br>{thought}</div>', unsafe_allow_html=True)
                final_text = parts[1].strip()
            else:
                final_text = raw_res.replace("<thinking>","").replace("</thinking>","").strip()

            # Image Detection Fix
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    p_str = match.group(1).strip()
                    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p_str)}?width=1024&height=1024&nologo=true&seed={np.random.randint(10000)}"
                    final_text = f"🎨 **Image Generated for:** {p_str}"

            st.markdown(final_text)
            if img_url: 
                st.image(img_url, use_container_width=True)
            
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url} if img_url else {"role": "assistant", "content": final_text})

        except Exception as e:
            st.error(f"Error: {e}")
            
