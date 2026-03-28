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

# --- 1. PREMIUM GEMINI LIGHT THEME ---
st.set_page_config(page_title="Nexus Flow Ultra", page_icon="🤖", layout="wide")

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

# --- 2. KEYS & INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("Missing API Keys in Secrets!")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

if "messages" not in st.session_state: st.session_state.messages = []
if "db" not in st.session_state: st.session_state.db = None

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:#1a73e8;'>Nexus Menu</h3>", unsafe_allow_html=True)
    if st.button("➕ New Chat Session"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()
    st.markdown("---")
    uploaded = st.file_uploader("Upload Study PDFs", type="pdf", accept_multiple_files=True)
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

# --- 4. HOME PAGE (ChatGPT Style) ---
if not st.session_state.messages:
    st.markdown("<div class='gemini-greeting'>Hi Sanjeev</div>", unsafe_allow_html=True)
    st.markdown("<div class='gemini-subtitle'>Where should we start?</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🖼️ Create Image"):
            st.session_state.messages.append({"role":"user", "content":"Create a beautiful 3D image of a futuristic computer lab"})
            st.rerun()
    with col2:
        if st.button("📝 Write Essay"):
            st.session_state.messages.append({"role":"user", "content":"Write a professional essay on the Importance of AI in Education"})
            st.rerun()
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m and m["image"]:
                st.image(m["image"], use_container_width=True)

# --- 5. CHAT LOGIC WITH STREAMING ---
if prompt := st.chat_input("Message Nexus..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # Context Search
            context = ""
            if st.session_state.db:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = st.session_state.db.search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([st.session_state.chunks[idx] for idx in I[0]])

            # Instructions with Emoji mandate
            sys_msg = f"""You are Nexus Flow Ultra. Use Hinglish naturally. 
            - FORMATTING: Answer like ChatGPT. Use bold headings, bullet points, and clean paragraphs. 
            - EMOJIS: Always use suitable emojis in every response like ChatGPT.
            - IMAGES: Use [GENERATE_IMAGE: prompt] only if asked to create/draw.
            Context: {context}"""
            
            # Using Llama-3.3 for best logic
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-10:]],
                stream=True
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            # Final Rendering without cursor
            response_placeholder.markdown(full_response)
            
            # Parsing Image if any
            img_url = None
            if "[GENERATE_IMAGE:" in full_response:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', full_response)
                if match:
                    p_str = match.group(1).strip()
                    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p_str)}?width=1024&height=1024&nologo=true&seed={random.randint(10000)}"
                    st.image(img_url, use_container_width=True)

            st.session_state.messages.append({"role": "assistant", "content": full_response, "image": img_url})

        except Exception as e:
            st.error(f"Error: {e}")
            
