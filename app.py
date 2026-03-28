import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import os

# --- 1. NEXUS CONFIG ---
st.set_page_config(page_title="Nexus Flow Ultra 🚀", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    .stChatMessage { border-radius: 15px; border: 1px solid #1E293B; margin: 10px 0; }
    .thinking-box { background-color: #161B22; border-left: 4px solid #00F5FF; padding: 12px; border-radius: 5px; color: #00F5FF; font-family: monospace; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API KEYS SETUP ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("⚠️ Keys Missing! Add GROQ_API_KEY and GOOGLE_API_KEY in Secrets.")
    st.stop()

# Initialize Clients
groq_client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# --- 3. RAG ENGINE (Google Embeddings + FAISS) ---
def process_knowledge(pdf_files):
    text = ""
    for pdf in pdf_files:
        reader = PdfReader(pdf)
        for page in reader.pages:
            text += page.extract_text() or ""
    
    chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
    # Google is very stable for embeddings
    embeddings = [genai.embed_content(model="models/embedding-001", content=c, task_type="retrieval_document")['embedding'] for c in chunks]
    
    index = faiss.IndexFlatL2(len(embeddings[0]))
    index.add(np.array(embeddings).astype('float32'))
    return index, chunks

# --- 4. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "nexus_brain" not in st.session_state:
    st.session_state.nexus_brain = None

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("⚡ Nexus Hub")
    st.caption("Powered by Groq (Llama 3 70B)")
    files = st.file_uploader("Upload Study PDFs", type="pdf", accept_multiple_files=True)
    if files and st.button("Sync Knowledge"):
        with st.spinner("Nexus is absorbing data..."):
            st.session_state.nexus_brain, st.session_state.chunks = process_knowledge(files)
            st.success("Brain Synced!")
    
    if st.button("🗑️ Reset All"):
        st.session_state.messages = []
        st.rerun()

# --- 6. CHAT INTERFACE ---
st.title("Nexus Flow Ultra 🚀")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m: st.image(m["image"])

# Response Logic
if prompt := st.chat_input("Ask Nexus..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # RAG Search
            context = ""
            if st.session_state.nexus_brain:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = st.session_state.nexus_brain.search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([st.session_state.chunks[i] for i in I[0] if i < len(st.session_state.chunks)])

            # Groq Llama 3 Call
            system_prompt = """
            You are Nexus Flow Ultra. 
            - LOGIC: For complex math/code, use <thinking> step-by-step reasoning </thinking> tags.
            - IMAGES: For image requests, use ONLY: [GENERATE_IMAGE: prompt in English].
            - LANGUAGE: Hinglish.
            - CONTEXT: Use provided context for answers if available.
            """
            
            completion = groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context: {context}\n\nQuestion: {prompt}"}
                ],
                temperature=0.7,
            )
            
            raw_res = completion.choices[0].message.content
            
            # Parsers
            final_text = raw_res
            img_url = None

            if "<thinking>" in raw_res:
                parts = raw_res.split("</thinking>")
                st.markdown(f'<div class="thinking-box">🔍 <b>Nexus Reasoning:</b><br>{parts[0].replace("<thinking>","").strip()}</div>', unsafe_allow_html=True)
                final_text = parts[1].strip()

            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(img_prompt)}?width=1024&height=1024&nologo=true"
                    final_text = f"🎨 **Visualizing:** {img_prompt}"

            st.markdown(final_text)
            if img_url: st.image(img_url)

            # Save History
            msg_data = {"role": "assistant", "content": final_text}
            if img_url: msg_data["image"] = img_url
            st.session_state.messages.append(msg_data)

        except Exception as e:
            st.error(f"Nexus Sync Error: {str(e)}")
            
