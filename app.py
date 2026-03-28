
import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import random

# --- 1. PREMIUM GEMINI UI ---
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
    }
    .stChatInput { border-radius: 30px !important; background-color: #f0f4f9 !important; border: none !important; }
    .thinking-box { background-color: #f1f3f4; border-radius: 12px; padding: 15px; color: #1a73e8; border-left: 5px solid #1a73e8; margin-bottom: 10px; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API KEYS & CLIENTS ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("API Keys missing! Check your Secrets.")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

if "messages" not in st.session_state: st.session_state.messages = []
if "db" not in st.session_state: st.session_state.db = None

# --- 3. SIDEBAR & PDF ENGINE ---
with st.sidebar:
    st.markdown("<h3 style='color:#1a73e8; text-align:center;'>Nexus Hub ⚡</h3>", unsafe_allow_html=True)
    if st.button("➕ Clear & New Chat"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()
    st.markdown("---")
    uploaded = st.file_uploader("Upload Knowledge (PDF)", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("🚀 Sync Knowledge"):
        text = ""
        for f in uploaded:
            reader = PdfReader(f)
            for page in reader.pages: text += page.extract_text() or ""
        chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
        embeddings = [genai.embed_content(model="models/embedding-001", content=c, task_type="retrieval_document")['embedding'] for c in chunks]
        index = faiss.IndexFlatL2(len(embeddings[0]))
        index.add(np.array(embeddings).astype('float32'))
        st.session_state.db, st.session_state.chunks = index, chunks
        st.success("Brain Synced! ✅")

# --- 4. CHAT INTERFACE ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m and m["image"]:
            st.image(m["image"], use_container_width=True)

# --- 5. CORE LOGIC ---
if prompt := st.chat_input("Ask Gemini..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # Context retrieval
            context = ""
            if st.session_state.db:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = st.session_state.db.search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([st.session_state.chunks[idx] for idx in I[0]])

            sys_msg = f"""
            You are Nexus Flow Ultra. 
            - LANGUAGE: Reply in the EXACT language of the user. 
            - EMOJIS: Use plenty of relevant emojis. 
            - IMAGES: Use [GENERATE_IMAGE: prompt in English] for visual requests. 
            - LOGIC: Use <thinking> for reasoning.
            Context: {context}
            """
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-6:]],
                stream=True
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            # --- ROBUST PARSER ---
            final_text = full_response
            if "<thinking>" in full_response:
                try:
                    parts = full_response.split("</thinking>")
                    thought = parts[0].replace("<thinking>","").strip()
                    st.markdown(f'<div class="thinking-box">🔍 <b>Nexus Reasoning:</b><br>{thought}</div>', unsafe_allow_html=True)
                    final_text = parts[1].strip()
                except:
                    final_text = full_response.replace("<thinking>","").replace("</thinking>","")

            response_placeholder.markdown(final_text)
            
            # --- IMAGE HANDLER (Fixing the 🖼️0 Error) ---
            img_url = None
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    # Final URL generation logic
                    encoded_prompt = urllib.parse.quote(img_prompt)
                    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={random.randint(0, 99999)}"
                    st.image(img_url, use_container_width=True)

            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": img_url})

        except Exception as e:
            st.error(f"Error: {e} ❌")
          
