import streamlit as st
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from pypdf import PdfReader
import urllib.parse
import re
import os

# --- 1. PAGE SETUP (Cyberpunk Generic Theme) ---
st.set_page_config(page_title="Nexus Flow AI 🤖", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .stChatMessage { border-radius: 12px; border: 1px solid #1E293B; margin: 8px 0; }
    .thinking-box { background-color: #1a1c23; border-left: 4px solid #00ffcc; padding: 10px; margin: 10px 0; color: #00ffcc; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API SETUP (Gemini API Key) ---
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    st.error("⚠️ API Key missing! Add GOOGLE_API_KEY in Hugging Face Secrets.")
    st.stop()

# --- 3. SYSTEM INSTRUCTION (All-in-One Bot) ---
instruction = """
You are Nexus Flow AI, a highly intelligent and versatile AI Assistant.
- GOAL: Help user with Coding, Math, SAT prep, Video Editing, etc.
- IMAGES: If user asks for an image, respond ONLY with: [GENERATE_IMAGE: descriptive prompt in English]
- THINKING: For complex tasks, use <thinking> step-by-step logic </thinking> then final answer.
- LANGUAGE: Use Hinglish if possible. Be neutral and helpful.
"""

# --- 4. RAG CORE (PDF Reading Logic) ---
def process_pdf(pdf_files):
    text = ""
    for pdf in pdf_files:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    
    # Text Chunks for RAG
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)
    
    # Google Embeddings
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_db = FAISS.from_texts(chunks, embeddings)
    return vector_db

# --- 5. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None

# --- 6. SIDEBAR (The Knowledge Center) ---
with st.sidebar:
    st.title("📂 External Memory")
    uploaded_files = st.file_uploader("Upload Knowledge (PDFs)", type="pdf", accept_multiple_files=True)
    
    if uploaded_files and st.button("Sync Documents"):
        with st.spinner("Learning from documents..."):
            st.session_state.vector_db = process_pdf(uploaded_files)
            st.success("Knowledge Base Updated!")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 7. MAIN UI ---
st.title("Nexus Flow AI 🤖")
st.caption("Advanced Chatbot | RAG, Image & Thinking Enabled")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m:
            st.image(m["image"])

# --- 8. SMART CHAT LOGIC ---
if prompt := st.chat_input("Kaise help karu aaj?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🔍 Nexus Flow is Analyzing...", expanded=False) as status:
            try:
                img_url = None
                
                # RAG vs GENERAL Mode
                if st.session_state.vector_db and re.search(r'(pdf|file|document|book)', prompt.lower()):
                    # RAG MODE: Specific context from PDF
                    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
                    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=st.session_state.vector_db.as_retriever())
                    res = qa_chain.invoke(prompt)
                    raw_res = res["result"]
                else:
                    # GENERAL MODE: Pure Gemini brain
                    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=instruction)
                    res = model.generate_content(prompt)
                    raw_res = res.text
                
                final_text = raw_res
                
                # Thinking Parsers
                if "<thinking>" in raw_res:
                    parts = raw_res.split("</thinking>")
                    thought = parts[0].replace("<thinking>", "").strip()
                    final_text = parts[1].strip()
                    st.markdown(f'<div class="thinking-box"><b>🧠 Reasoning Step:</b><br>{thought}</div>', unsafe_allow_html=True)

                # Image Generation Parsers
                if "[GENERATE_IMAGE:" in final_text:
                    match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                    if match:
                        img_prompt = match.group(1).strip()
                        encoded_prompt = urllib.parse.quote(img_prompt)
                        img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
                        final_text = f"🎨 **Image Generated for:** {img_prompt}"
                
                status.update(label="✅ Analysis Done!", state="complete")
            except Exception as e:
                final_text = f"❌ Error: {str(e)}"
                status.update(label="Critical Error", state="error")

        st.markdown(final_text)
        if img_url: st.image(img_url)
        
        # Save to memory
        msg_data = {"role": "assistant", "content": final_text}
        if img_url: msg_data["image"] = img_url
        st.session_state.messages.append(msg_data)
        
