import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import os

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Nexus Flow AI", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .thinking-box { background-color: #1a1c23; border-left: 4px solid #00ffcc; padding: 10px; margin: 10px 0; color: #00ffcc; font-family: monospace; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API SETUP ---
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ API Key missing! Add GOOGLE_API_KEY in Streamlit Secrets.")
    st.stop()

# --- 3. CORE LOGIC (PDF & Embeddings without LangChain) ---
def get_pdf_text(pdf_files):
    text = ""
    for pdf in pdf_files:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    return text

def create_vector_db(text):
    # Text Splitter Logic
    chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
    
    # Get Embeddings using Pure Gemini
    embeddings = []
    for chunk in chunks:
        result = genai.embed_content(model="models/embedding-001", content=chunk, task_type="retrieval_document")
        embeddings.append(result['embedding'])
    
    # FAISS Index
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))
    return index, chunks

def search_docs(query, index, chunks):
    query_emb = genai.embed_content(model="models/embedding-001", content=query, task_type="retrieval_query")['embedding']
    D, I = index.search(np.array([query_emb]).astype('float32'), k=3)
    context = "\n".join([chunks[i] for i in I[0] if i < len(chunks)])
    return context

# --- 4. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "index" not in st.session_state:
    st.session_state.index = None
    st.session_state.chunks = None

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("📂 Knowledge Base")
    uploaded = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("Sync Documents"):
        with st.spinner("Learning..."):
            raw_text = get_pdf_text(uploaded)
            st.session_state.index, st.session_state.chunks = create_vector_db(raw_text)
            st.success("Synced Successfully!")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 6. MAIN UI & CHAT ---
st.title("Nexus Flow AI 🤖")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m: st.image(m["image"])

if prompt := st.chat_input("How can I help you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # System Instruction for Image & Thinking
            sys_inst = "You are Nexus Flow AI. Use Hinglish. For images respond only with [GENERATE_IMAGE: prompt]. Use <thinking> for logic."
            
            context = ""
            if st.session_state.index:
                context = search_docs(prompt, st.session_state.index, st.session_state.chunks)
            
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=sys_inst)
            full_prompt = f"Context: {context}\n\nUser Question: {prompt}" if context else prompt
            
            res = model.generate_content(full_prompt).text
            
            # Parsers
            final_text = res
            img_url = None

            if "<thinking>" in res:
                parts = res.split("</thinking>")
                st.markdown(f'<div class="thinking-box"><b>🧠 Logic:</b><br>{parts[0].replace("<thinking>","").strip()}</div>', unsafe_allow_html=True)
                final_text = parts[1].strip()

            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(img_prompt)}?width=1024&height=1024&nologo=true"
                    final_text = f"🎨 **Visualizing:** {img_prompt}"

            st.markdown(final_text)
            if img_url: st.image(img_url)

            msg = {"role": "assistant", "content": final_text}
            if img_url: msg["image"] = img_url
            st.session_state.messages.append(msg)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            
