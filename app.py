import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import os

# --- 1. NEXUS PREMIUM THEME (Gemini/ChatGPT Style) ---
st.set_page_config(page_title="Nexus Flow Ultra v4.2", page_icon="🤖", layout="wide")

# Custom CSS for Gemini Dark Look
st.markdown("""
    <style>
    /* Main Background Gradient */
    .stApp {
        background: radial-gradient(circle at top right, #1e293b, #0e1117, #020617);
        color: #e0e0e0;
    }

    /* Message Bubbles (Rounded cards) */
    .stChatMessage {
        background: rgba(30, 41, 59, 0.4) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        padding: 15px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }

    /* Sidebar Glassmorphism effect */
    [data-testid="stSidebar"] {
        background-color: rgba(17, 20, 26, 0.85) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Neon Accent Button */
    .stButton>button {
        background: linear-gradient(90deg, #00f5ff, #7000ff) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        transition: 0.3s all ease-in-out !important;
    }
    .stButton>button:hover {
        box-shadow: 0 0 20px rgba(0, 245, 255, 0.5);
        transform: scale(1.02);
    }

    /* Thinking box */
    .thinking-box {
        background: rgba(0, 245, 255, 0.05);
        border-left: 4px solid #00f5ff;
        padding: 15px;
        border-radius: 8px;
        color: #00f5ff;
        font-family: monospace;
        margin-bottom: 10px;
    }

    /* Chat Input Styling */
    .stChatInput {
        border-radius: 30px !important;
        border: 1px solid rgba(0, 245, 255, 0.2) !important;
        background: #1e293b !important;
    }

    /* Gradient Title */
    .nexus-title {
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(to right, #00f5ff, #bfdbfe, #7000ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        letter-spacing: -2px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KEYS & INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("Missing API Keys! Add GROQ_API_KEY and GOOGLE_API_KEY in Secrets.")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# --- 3. MULTI-USER STORAGE ---
if "all_users" not in st.session_state:
    st.session_state.all_users = {"Sanjeev": {"messages": [], "db": None, "chunks": None}}

if "current_user" not in st.session_state:
    st.session_state.current_user = "Sanjeev"

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

# --- 5. SIDEBAR (Control Center) ---
with st.sidebar:
    st.markdown("<h2 style='color:#00f5ff; text-align:center;'>⚡ Nexus Hub</h2>", unsafe_allow_html=True)
    
    st.session_state.current_user = st.selectbox("Switch User Account", list(st.session_state.all_users.keys()))
    user_data = st.session_state.all_users[st.session_state.current_user]
    
    if st.button("➕ Create New Account"):
        new_name = f"User_{len(st.session_state.all_users)+1}"
        st.session_state.all_users[new_name] = {"messages": [], "db": None, "chunks": None}
        st.rerun()

    st.markdown("---")
    st.subheader("📂 PDF Knowledge")
    uploaded = st.file_uploader(f"Upload PDFs for {st.session_state.current_user}", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("🚀 Sync Brain"):
        with st.spinner("Processing documents..."):
            user_data["db"], user_data["chunks"] = process_pdfs(uploaded)
            st.success("Docs synced!")
            
    st.markdown("---")
    if st.button("🗑️ Clear Current Chat"):
        user_data["messages"] = []
        user_data["db"] = None
        st.rerun()

# --- 6. MAIN CHAT & HOME PAGE ---
curr_user = st.session_state.current_user
messages = user_data["messages"]

if not messages:
    # Beautiful Gemini-style Home Page
    st.markdown("<div class='nexus-title'>Nexus Flow Ultra</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#94a3b8;'>Advanced Multimodal Intelligence</p>", unsafe_allow_html=True)
    
    # Action Cards (Suggestions)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎨 Create a futuristic CS engineering lab image"):
            st.session_state.messages.append({"role":"user", "content":"Futuristic CS Lab photo, neon coding style"})
            st.rerun()
    with col2:
        if st.button("🧠 Solve a tough coding problem step-by-step"):
            st.session_state.messages.append({"role":"user", "content":"Python recursion ka mushkil logic thinking mode mein samjhao"})
            st.rerun()
    st.markdown("---")

else:
    # Display History
    for m in messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m: st.image(m["image"], use_container_width=True)

# --- 7. CHAT LOGIC (Fixed Model & Language) ---
if prompt := st.chat_input(f"Ask Nexus as {curr_user}..."):
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Context Search
            context = ""
            if user_data["db"]:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = user_data["db"].search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([user_data["chunks"][idx] for idx in I[0]])

            sys_msg = f"You are Nexus Flow Ultra. Use Hinglish naturally. Reply in user's language. Use <thinking> for logic. Use [GENERATE_IMAGE: prompt] for photos. Context: {context}"
            
            # Using stable history context
            hist = [{"role": m["role"], "content": m["content"]} for m in messages[-10:]]
            
            # FIXED MODEL: Using llama-3.3-70b-versatile
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + hist,
                temperature=0.7
            )
            
            raw_res = response.choices[0].message.content
            final_text, img_url = raw_res, None

            # Parsers
            if "<thinking>" in raw_res:
                parts = raw_res.split("</thinking>")
                st.markdown(f'<div class="thinking-box">🔍 <b>Nexus Logic:</b><br>{parts[0].replace("<thinking>","").strip()}</div>', unsafe_allow_html=True)
                final_text = parts[1].strip()

            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    p_str = match.group(1).strip()
                    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p_str)}?width=1024&height=1024&nologo=true"
                    final_text = f"🎨 **Creating image for:** {p_str}"

            st.markdown(final_text)
            if img_url: st.image(img_url, use_container_width=True)
            
            # Save History
            msg_data = {"role": "assistant", "content": final_text}
            if img_url: msg_data["image"] = img_url
            messages.append(msg_data)

        except Exception as e:
            st.error(f"Nexus Sync Error: {e}")
            
