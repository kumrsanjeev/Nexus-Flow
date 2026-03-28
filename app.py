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

# Custom CSS to match Gemini's exact look
st.markdown("""
    <style>
    /* Gemini White Theme */
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #f0f4f9 !important;
        border-right: none;
    }

    /* Gemini style message bubbles */
    .stChatMessage {
        background-color: transparent !important;
        border: none !important;
        padding: 10px 0 !important;
    }
    
    /* Suggested Buttons (Pills) */
    .stButton>button {
        background-color: #ffffff !important;
        color: #444746 !important;
        border: 1px solid #c4c7c5 !important;
        border-radius: 25px !important;
        padding: 8px 20px !important;
        font-weight: 500 !important;
        text-align: left !important;
        display: block;
        margin-bottom: 8px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #f1f3f4 !important;
        border-color: #1a73e8 !important;
    }

    /* Thinking box (Logic) */
    .thinking-box {
        background-color: #f0f4f9;
        border-radius: 12px;
        padding: 15px;
        color: #0b57d0;
        font-size: 0.9rem;
        border-left: 4px solid #0b57d0;
        margin: 10px 0;
    }

    /* Gemini Title Style */
    .gemini-greeting {
        font-size: 2.8rem;
        font-weight: 500;
        color: #1f1f1f;
        margin-top: 50px;
    }
    .gemini-subtitle {
        font-size: 2.5rem;
        font-weight: 500;
        color: #c4c7c5;
        margin-bottom: 30px;
    }

    /* Chat Input Styling */
    .stChatInputContainer { padding-bottom: 30px; }
    .stChatInput {
        border-radius: 30px !important;
        background-color: #f0f4f9 !important;
        border: none !important;
    }
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

# --- 3. PERSISTENT STORAGE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "db" not in st.session_state: st.session_state.db = None

# --- 4. ENGINE FUNCTIONS ---
def process_pdfs(files):
    text = ""
    for f in files:
        reader = PdfReader(f)
        for page in reader.pages: text += page.extract_text() or ""
    chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
    embeddings = [genai.embed_content(model="models/embedding-001", content=c, task_type="retrieval_document")['embedding'] for c in chunks]
    index = faiss.IndexFlatL2(len(embeddings[0]))
    index.add(np.array(embeddings).astype('float32'))
    return index, chunks

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:#1a73e8;'>Menu</h3>", unsafe_allow_html=True)
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()
    
    st.markdown("---")
    st.write("📂 **Docs Knowledge**")
    uploaded = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("Sync Brain"):
        st.session_state.db, st.session_state.chunks = process_pdfs(uploaded)
        st.success("Synced! ✅")

# --- 6. MAIN INTERFACE (Gemini Clone) ---
if not st.session_state.messages:
    st.markdown("<div class='gemini-greeting'>Hi Sanjeev</div>", unsafe_allow_html=True)
    st.markdown("<div class='gemini-subtitle'>Where should we start?</div>", unsafe_allow_html=True)
    
    # Suggested Pills (Buttons)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🖼️ Create image"):
            st.session_state.messages.append({"role":"user", "content":"Create a beautiful image of a space station 🚀"})
            st.rerun()
        if st.button("🏏 Follow IPL"):
            st.session_state.messages.append({"role":"user", "content":"IPL latest updates aur highlights batao 🏏"})
            st.rerun()
    with col2:
        if st.button("📝 Write anything"):
            st.session_state.messages.append({"role":"user", "content":"Ek computer science engineer ke liye career advice likho 📝"})
            st.rerun()
        if st.button("🎸 Create music"):
            st.session_state.messages.append({"role":"user", "content":"Music generate karne ka idea do 🎸"})
            st.rerun()
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m: st.image(m["image"], use_container_width=True)

# --- 7. CHAT LOGIC (Fixed & Robust) ---
if prompt := st.chat_input("Ask Gemini"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Context Logic
            context = ""
            if st.session_state.db:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = st.session_state.db.search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([st.session_state.chunks[idx] for idx in I[0]])

            sys_msg = f"You are Nexus Flow Ultra (Gemini Clone). Reply in user's language. Use Hinglish. Use <thinking> only for logic. For images use [GENERATE_IMAGE: prompt]. Context: {context}"
            
            # Using Llama 3.3 for superior reliability
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-6:]]
            )
            
            raw_res = response.choices[0].message.content
            final_text, img_url = raw_res, None

            # --- ROBUST PARSER (Fixed Index Out of Range) ---
            if "<thinking>" in raw_res and "</thinking>" in raw_res:
                try:
                    parts = raw_res.split("</thinking>")
                    thought = parts[0].replace("<thinking>","").strip()
                    st.markdown(f'<div class="thinking-box">🔍 <b>Reasoning:</b><br>{thought}</div>', unsafe_allow_html=True)
                    final_text = parts[1].strip()
                except:
                    final_text = raw_res.replace("<thinking>","").replace("</thinking>","")
            else:
                final_text = raw_res

            # Image logic
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    p_str = match.group(1).strip()
                    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p_str)}?width=1024&height=1024&nologo=true"
                    final_text = f"🎨 **Creating image for:** {p_str}"

            st.markdown(final_text)
            if img_url: st.image(img_url, use_container_width=True)
            
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url} if img_url else {"role": "assistant", "content": final_text})

        except Exception as e:
            st.error(f"Error: {e}")
            
