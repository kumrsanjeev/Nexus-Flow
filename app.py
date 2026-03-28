import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import time

# --- 1. PREMIUM CHATGPT/GEMINI UI ---
st.set_page_config(page_title="Nexus Flow Ultra", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    /* ChatGPT Light/Clean Theme */
    .stApp { background-color: #ffffff; color: #37352f; }
    [data-testid="stSidebar"] { background-color: #f7f7f8 !important; border-right: 1px solid #d1d5db; }
    
    /* Message Bubbles */
    .stChatMessage {
        border-radius: 12px;
        padding: 1.5rem !important;
        margin-bottom: 1rem;
        line-height: 1.6;
    }
    
    /* AI Response Formatting */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #111827; font-weight: 700; margin-top: 1rem; }
    .stMarkdown p { font-size: 1.1rem; color: #374151; }
    
    /* Suggested Pill Buttons */
    .stButton>button {
        background-color: #ffffff !important;
        color: #4b5563 !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 20px !important;
        padding: 0.5rem 1.2rem !important;
        font-weight: 500 !important;
        transition: 0.2s;
    }
    .stButton>button:hover { background-color: #f9fafb !important; border-color: #1a73e8 !important; color: #1a73e8 !important; }

    /* Input Box Styling */
    .stChatInputContainer { padding-bottom: 2rem; }
    .stChatInput { border-radius: 26px !important; border: 1px solid #e5e7eb !important; background: #fff !important; }

    /* Custom Header */
    .main-header { font-size: 2.5rem; font-weight: 600; text-align: center; margin-top: 2rem; color: #1f2937; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZATION ---
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
    st.markdown("<h3 style='text-align:center;'>Nexus Hub</h3>", unsafe_allow_html=True)
    if st.button("➕ New Chat"):
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
    st.markdown("<div class='main-header'>What can I help with?</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🖼️ Create Image"):
            st.session_state.messages.append({"role":"user", "content":"Create a beautiful 3D image of a futuristic computer lab"})
            st.rerun()
    with col2:
        if st.button("📝 Write Essay"):
            st.session_state.messages.append({"role":"user", "content":"Write a professional essay on the Importance of AI in Education"})
            st.rerun()
    with col3:
        if st.button("🧠 SAT Practice"):
            st.session_state.messages.append({"role":"user", "content":"Give me a tough SAT math logic question"})
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
            context = ""
            if st.session_state.db:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = st.session_state.db.search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([st.session_state.chunks[idx] for idx in I[0]])

            sys_msg = f"""You are Nexus Flow Ultra. 
            - FORMATTING: Answer like ChatGPT. Use bold headings, bullet points, and clean paragraphs. 
            - LANGUAGE: Reply in the user's language.
            - IMAGES: Use [GENERATE_IMAGE: prompt in English] only if asked to create/draw.
            Context: {context}"""
            
            # Using Llama-3.3 for high-quality logic
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-6:]],
                stream=True # Streaming ON
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
                    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p_str)}?width=1024&height=1024&nologo=true&seed={np.random.randint(10000)}"
                    st.image(img_url, use_container_width=True)

            st.session_state.messages.append({"role": "assistant", "content": full_response, "image": img_url})

        except Exception as e:
            st.error(f"Error: {e}")
            
