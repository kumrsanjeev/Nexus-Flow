import streamlit as st
import google.generativeai as genai
from groq import Groq
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import time

# --- 1. NEXUS CONFIG & THEME ---
st.set_page_config(page_title="Nexus Flow Ultra v3.0", page_icon="⚡", layout="wide")

# Modern ChatGPT/Gemini-like Styling
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle, #1a1c23 0%, #0e1117 100%); color: #e0e0e0; }
    .stChatMessage { border-radius: 20px; border: 1px solid #30363d; padding: 15px; margin-bottom: 10px; transition: 0.3s; }
    .stChatMessage:hover { border-color: #00ffcc; box-shadow: 0 0 10px rgba(0, 255, 204, 0.2); }
    .thinking-box { background-color: #0d1117; border-left: 4px solid #00f5ff; padding: 15px; margin: 10px 0; color: #00f5ff; font-family: 'Courier New', monospace; border-radius: 8px; font-size: 0.9em; }
    .stButton>button { background: linear-gradient(45deg, #00ffcc, #0088ff); color: white; border: none; border-radius: 10px; font-weight: bold; width: 100%; transition: 0.3s; }
    .stButton>button:hover { box-shadow: 0 0 15px rgba(0, 255, 204, 0.6); transform: translateY(-2px); }
    [data-testid="stSidebar"] { background-color: #11141a; border-right: 1px solid #1e293b; }
    .stFileUploader label { color: #00ffcc; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API & ENGINE ---
# Secrets check
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("⚠️ API Keys Missing! Please add GROQ_API_KEY and GOOGLE_API_KEY in Streamlit Secrets.")
    st.markdown("---")
    st.info("💡 Keys daalne ke baad app apne aap reload ho jayega.")
    st.stop()

# Initialize clients
try:
    groq_client = Groq(api_key=groq_key)
    genai.configure(api_key=google_key)
except Exception as e:
    st.error(f"❌ API Initialization Error: {e}")
    st.stop()

# System Persona
NEXUS_SYSTEM_PROMPT = """
You are Nexus Flow Ultra v3.0, a highly advanced AI.
- TONE: Professional, slightly witty, and deeply helpful (Hinglish).
- IMAGES: If user asks for an image, respond ONLY with: [GENERATE_IMAGE: descriptive prompt in English].
- REASONING: Explain complex logic/code inside <thinking> step-by-step logic </thinking> tags.
- FORMATTING: Use bold text, tables, and code blocks to make answers readable.
- PDF: If context is provided from PDF, prioritize it. Use general knowledge to fill gaps.
"""

def get_pdf_content(files):
    text = ""
    for f in files:
        reader = PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

def setup_vector_store(text):
    chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
    embeddings = [genai.embed_content(model="models/embedding-001", content=c, task_type="retrieval_document")['embedding'] for c in chunks]
    index = faiss.IndexFlatL2(len(embeddings[0]))
    index.add(np.array(embeddings).astype('float32'))
    return index, chunks

# --- 3. SESSION STATE ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "index" not in st.session_state:
    st.session_state.index = None
    st.session_state.chunks = None

# --- 4. SIDEBAR (Control Center) ---
with st.sidebar:
    st.title("⚡ Nexus Hub")
    st.caption("Powered by Llama 3 (70B) & Gemini Embeddings")
    st.markdown("---")
    
    st.info("Goal: 1500+ SAT | Computer Science Pro")
    
    # Elegant File Uploader as the "Add Photo/Doc" button alternative
    uploaded = st.file_uploader("📥 Add Knowledge (PDFs)", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("🚀 Sync Nexus Brain"):
        with st.spinner("Learning from documents..."):
            raw_text = get_pdf_content(uploaded)
            st.session_state.index, st.session_state.chunks = setup_vector_store(raw_text)
            st.success("Docs Synced!")
    
    st.markdown("---")
    if st.button("🧹 Clear Conversation"):
        st.session_state.chat_history = []
        st.rerun()

# --- 5. CHAT INTERFACE & HOME PAGE ---
if not st.session_state.chat_history:
    # --- Home Page Logic ---
    st.title("Welcome to Nexus Flow Ultra 🤖")
    st.markdown("""
        I'm your **Next-Generation Multi-Modal AI**. I can logic, reason, generate images, and learn from your documents.
        How can I help you today, Sanjeev?
    """)
    st.markdown("### 🌟 Suggested Starting Points")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎨 Generate Futuristic Computer Science Lab Image"):
            st.session_state.chat_history.append({"role": "user", "content": "Futuristic Computer Science Lab ki photo banao"})
            st.rerun()
        if st.button("🧠 Solve complex SAT Math logic problem"):
            st.session_state.chat_history.append({"role": "user", "content": "SAT Math logic question solve karo jisme thinking mode active ho"})
            st.rerun()
    with col2:
        if st.button("📂 Explain how PDF analysis (RAG) works here"):
            st.session_state.chat_history.append({"role": "user", "content": "Is bot mein PDF analysis (RAG) kaise kaam karta hai?"})
            st.rerun()
        if st.button("💻 How can you help me with Python/C++?"):
            st.session_state.chat_history.append({"role": "user", "content": "Python/C++ programming mein kaise help karoge?"})
            st.rerun()
    st.markdown("---")

else:
    # Display History
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m: st.image(m["image"])

# Input Handling
if prompt := st.chat_input("Ask Nexus..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # RAG Search
            context = ""
            if st.session_state.index:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = st.session_state.index.search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([st.session_state.chunks[i] for i in I[0] if i < len(st.session_state.chunks)])

            # Generation via Groq (Super Fast)
            completion = groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": NEXUS_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Context: {context}\n\nQuestion: {prompt}"}
                ],
                temperature=0.6,
            )
            
            raw_res = completion.choices[0].message.content
            
            final_text = raw_res
            img_url = None

            # Thinking Parser
            if "<thinking>" in raw_res:
                parts = raw_res.split("</thinking>")
                thought = parts[0].replace("<thinking>", "").strip()
                st.markdown(f'<div class="thinking-box">🔍 <b>Nexus Reasoning:</b><br>{thought}</div>', unsafe_allow_html=True)
                final_text = parts[1].strip()

            # Image Parser
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    encoded = urllib.parse.quote(img_prompt)
                    img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"
                    final_text = f"🎨 **Visualizing:** {img_prompt}"

            st.markdown(final_text)
            if img_url: st.image(img_url)

            # Store memory
            msg_data = {"role": "assistant", "content": final_text}
            if img_url: msg_data["image"] = img_url
            st.session_state.chat_history.append(msg_data)
            
        except Exception as e:
            st.error(f"❌ Nexus Error: {str(e)}")
            
