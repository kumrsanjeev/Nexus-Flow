import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import os

# --- 1. NEXUS PREMIUM LIGHT THEME ---
st.set_page_config(page_title="Nexus Flow Ultra", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; color: #1f1f1f; }
    [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e0e0e0; }
    .stChatMessage { border-radius: 15px; border: 1px solid #e0e0e0 !important; background-color: #ffffff !important; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .thinking-box { background: #f1f3f4; border-left: 4px solid #1a73e8; padding: 12px; border-radius: 8px; color: #1a73e8; font-size: 0.85rem; margin-bottom: 10px; }
    .nexus-title { font-size: 2.5rem; font-weight: 800; color: #1a73e8; text-align: center; }
    .stButton>button { border-radius: 20px !important; background: #1a73e8 !important; color: white !important; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KEYS & INITIALIZATION ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("Missing API Keys!")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# --- 3. MULTI-USER STORAGE ---
if "all_users" not in st.session_state:
    st.session_state.all_users = {"Sanjeev": {"messages": [], "db": None, "chunks": None}}

if "current_user" not in st.session_state:
    st.session_state.current_user = "Sanjeev"

# --- 4. CORE FUNCTIONS ---
def process_knowledge(files):
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
    st.markdown("<h2 style='color:#1a73e8;'>⚡ Nexus Hub</h2>", unsafe_allow_html=True)
    st.session_state.current_user = st.selectbox("User Account", list(st.session_state.all_users.keys()))
    user_data = st.session_state.all_users[st.session_state.current_user]
    
    if st.button("➕ New User"):
        new_u = f"User_{len(st.session_state.all_users)+1}"
        st.session_state.all_users[new_u] = {"messages": [], "db": None, "chunks": None}
        st.rerun()
    
    st.markdown("---")
    uploaded = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("Sync Brain"):
        user_data["db"], user_data["chunks"] = process_knowledge(uploaded)
        st.success("Synced!")

# --- 6. CHAT INTERFACE ---
curr_user = st.session_state.current_user
messages = user_data["messages"]

if not messages:
    st.markdown(f"<div class='nexus-title'>Namaste, {curr_user} 🙏</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#5f6368;'>Main aapke language aur context ke hisab se reply dunga.</p>", unsafe_allow_html=True)
else:
    for m in messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m: st.image(m["image"], use_container_width=True)

# --- 7. CHAT LOGIC (Language Adaptive Fix) ---
if prompt := st.chat_input(f"Ask Nexus..."):
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            context = ""
            if user_data["db"]:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = user_data["db"].search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([user_data["chunks"][idx] for idx in I[0]])

            # Instructions Fix: Language matching + Direct Answer
            sys_msg = f"""
            You are Nexus Flow Ultra. 
            - LANGUAGE RULE: Reply in the SAME language as the user's question. If user asks in Hindi, reply in Hindi. If English, reply in English. 
            - DIRECTNESS: Answer the core question directly. (Example: "Pm of India" -> "Narendra Modi").
            - LOGIC: Use <thinking> tags ONLY for complex logic.
            - IMAGES: Use [GENERATE_IMAGE: descriptive prompt in English].
            - PDF Context: {context}
            """
            
            # Using Llama-3.1-70b-versatile for better language understanding
            response = client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + [{"role": m["role"], "content": m["content"]} for m in messages[-6:]],
                temperature=0.7
            )
            
            raw_res = response.choices[0].message.content
            final_text, img_url = raw_res, None

            # --- SAFE PARSER (No more list index error) ---
            if "<thinking>" in raw_res and "</thinking>" in raw_res:
                parts = raw_res.split("</thinking>")
                thought = parts[0].replace("<thinking>","").strip()
                st.markdown(f'<div class="thinking-box">🔍 <b>Nexus Logic:</b><br>{thought}</div>', unsafe_allow_html=True)
                final_text = parts[1].strip()
            else:
                final_text = raw_res.replace("<thinking>", "").replace("</thinking>", "").strip()

            # --- IMAGE GENERATION FIX ---
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    p_str = match.group(1).strip()
                    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p_str)}?width=1024&height=1024&nologo=true"
                    final_text = f"🎨 **Image for:** {p_str}"

            st.markdown(final_text)
            if img_url: st.image(img_url, use_container_width=True)
            
            # Save
            msg_data = {"role": "assistant", "content": final_text}
            if img_url: msg_data["image"] = img_url
            messages.append(msg_data)

        except Exception as e:
            st.error(f"Nexus Error: {e}")
            
