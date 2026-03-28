import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import os

# --- 1. NEXUS LIGHT THEME ---
st.set_page_config(page_title="Nexus Flow Multi-User", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; color: #1f1f1f; }
    [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e0e0e0; }
    .stChatMessage { border-radius: 15px; border: 1px solid #e0e0e0 !important; background-color: #ffffff !important; margin-bottom: 12px; }
    .user-tag { background: #1a73e8; color: white; padding: 2px 10px; border-radius: 10px; font-size: 0.8rem; }
    .nexus-title { font-size: 2.8rem; font-weight: 800; color: #1a73e8; text-align: center; }
    .stButton>button { border-radius: 20px !important; background: #1a73e8 !important; color: white !important; width: 100%; }
    .thinking-box { background: #f1f3f4; border-left: 4px solid #1a73e8; padding: 12px; border-radius: 8px; color: #1a73e8; font-size: 0.85rem; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KEYS SETUP ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("API Keys missing in Secrets!")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# --- 3. MULTI-USER STORAGE LOGIC ---
# Hum 'all_users' mein sabka data alag-alag rakhenge
if "all_users" not in st.session_state:
    st.session_state.all_users = {
        "Sanjeev": {"messages": [], "db": None, "chunks": None},
        "Guest": {"messages": [], "db": None, "chunks": None}
    }

if "current_user" not in st.session_state:
    st.session_state.current_user = "Sanjeev"

# --- 4. ENGINE FUNCTIONS ---
def process_pdfs(files):
    text = ""
    for f in files:
        reader = PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
    embeddings = [genai.embed_content(model="models/embedding-001", content=c, task_type="retrieval_document")['embedding'] for c in chunks]
    index = faiss.IndexFlatL2(len(embeddings[0]))
    index.add(np.array(embeddings).astype('float32'))
    return index, chunks

# --- 5. SIDEBAR (User Switcher & History) ---
with st.sidebar:
    st.markdown("<h2 style='color:#1a73e8;'>⚡ Nexus Hub</h2>", unsafe_allow_html=True)
    
    # User Selection
    st.session_state.current_user = st.selectbox("Switch User Account", list(st.session_state.all_users.keys()))
    user_data = st.session_state.all_users[st.session_state.current_user]
    
    if st.button("➕ Create New Account"):
        new_name = f"User_{len(st.session_state.all_users)+1}"
        st.session_state.all_users[new_name] = {"messages": [], "db": None, "chunks": None}
        st.rerun()

    st.markdown("---")
    if st.button("🗑️ Clear Current Chat"):
        user_data["messages"] = []
        user_data["db"] = None
        st.rerun()

    st.markdown("---")
    st.subheader("📂 PDF Knowledge")
    uploaded = st.file_uploader(f"Upload for {st.session_state.current_user}", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("Sync Brain"):
        with st.spinner("Processing..."):
            user_data["db"], user_data["chunks"] = process_pdfs(uploaded)
            st.success("Brain Synced!")

# --- 6. MAIN CHAT INTERFACE ---
curr_user = st.session_state.current_user
messages = user_data["messages"]

if not messages:
    st.markdown(f"<div class='nexus-title'>Hello, {curr_user} 👋</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#5f6368;'>Aapka personal Nexus account active hai.</p>", unsafe_allow_html=True)
else:
    for m in messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m:
                st.image(m["image"], use_container_width=True)

# --- 7. CHAT LOGIC ---
if prompt := st.chat_input(f"Ask Nexus anything as {curr_user}..."):
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # PDF Context Search
            context = ""
            if user_data["db"]:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = user_data["db"].search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([user_data["chunks"][idx] for idx in I[0]])

            sys_msg = f"You are Nexus Flow Ultra. User: {curr_user}. Use Hinglish. Use <thinking> for logic. Use [GENERATE_IMAGE: prompt] for photos. Context: {context}"
            hist = [{"role": m["role"], "content": m["content"]} for m in messages[-10:]]
            
            # Groq Call
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + hist,
                temperature=0.7
            )
            
            raw_res = response.choices[0].message.content
            final_text, img_url = raw_res, None

            # Logic Parsers
            if "<thinking>" in raw_res:
                parts = raw_res.split("</thinking>")
                st.markdown(f'<div class="thinking-box">🔍 <b>Nexus Logic:</b><br>{parts[0].replace("<thinking>","").strip()}</div>', unsafe_allow_html=True)
                final_text = parts[1].strip()

            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    p_str = match.group(1).strip()
                    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p_str)}?width=1024&height=1024&nologo=true"
                    final_text = f"🎨 **Creating Image:** {p_str}"

            st.markdown(final_text)
            if img_url: st.image(img_url, use_container_width=True)
            
            # Save to memory
            msg_data = {"role": "assistant", "content": final_text}
            if img_url: msg_data["image"] = img_url
            messages.append(msg_data)

        except Exception as e:
            st.error(f"Nexus Error: {e}")
            
