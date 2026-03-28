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

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Nexus Flow Pro 🤖", page_icon="⚡", layout="wide")

# Cyberpunk Generic Theme
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    .stChatMessage { border-radius: 12px; border: 1px solid #262730; margin: 8px 0; }
    .thinking-box { background-color: #161B22; border-left: 4px solid #58A6FF; padding: 12px; margin: 10px 0; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 0.9em; color: #8B949E; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API KEY SETUP ---
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    st.error("⚠️ API Key missing! Add GOOGLE_API_KEY in Secrets.")
    st.stop()

# --- 3. SYSTEM INSTRUCTION (Generic AI) ---
instruction = """
You are a highly capable and versatile AI Assistant.
- GOAL: Provide accurate and helpful information on any topic (Coding, Math, SAT, Video Editing, etc.).
- STYLE: Professional, clear, and adaptive. Use Hinglish if the user prefers.
- REASONING: Explain your logic inside <thinking> tags before giving complex answers.
- IMAGES: If asked for a visual/image, respond with: [GENERATE_IMAGE: detailed prompt]
"""

# --- 4. RAG ENGINE ---
def process_pdf(pdf_files):
    text = ""
    for pdf in pdf_files:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_db = FAISS.from_texts(chunks, embeddings)
    return vector_db

# --- 5. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None

# --- 6. SIDEBAR ---
with st.sidebar:
    st.title("📂 External Memory")
    uploaded_files = st.file_uploader("Upload Knowledge (PDFs)", type="pdf", accept_multiple_files=True)
    if uploaded_files and st.button("Sync Knowledge"):
        with st.spinner("Processing Documents..."):
            st.session_state.vector_db = process_pdf(uploaded_files)
            st.success("Knowledge Base Updated!")
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

# --- 7. UI DISPLAY ---
st.title("Nexus Flow Pro 🤖")
st.caption("Advanced Generic AI | RAG & Image Enabled")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m:
            st.image(m["image"])

# --- 8. SMART LOGIC ---
if prompt := st.chat_input("How can I help you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🔍 Processing...", expanded=True) as status:
            try:
                img_url = None
                if st.session_state.vector_db:
                    # RAG Mode
                    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
                    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=st.session_state.vector_db.as_retriever())
                    res = qa_chain.invoke(prompt)
                    raw_res = res["result"]
                else:
                    # Normal Mode
                    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=instruction)
                    res = model.generate_content(prompt)
                    raw_res = res.text

                # Thinking & Image Parsers
                if "<thinking>" in raw_res:
                    parts = raw_res.split("</thinking>")
                    thought = parts[0].replace("<thinking>", "").strip()
                    final_text = parts[1].strip()
                    st.markdown(f'<div class="thinking-box"><b>Reasoning:</b><br>{thought}</div>', unsafe_allow_html=True)
                else:
                    final_text = raw_res

                if "[GENERATE_IMAGE:" in final_text:
                    match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                    if match:
                        img_prompt = match.group(1).strip()
                        encoded_prompt = urllib.parse.quote(img_prompt)
                        img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
                        final_text = f"🎨 **Image Generated for:** {img_prompt}"

                status.update(label="✅ Complete", state="complete", expanded=False)
            except Exception as e:
                final_text = f"❌ Error: {str(e)}"
                status.update(label="Error", state="error")

        st.markdown(final_text)
        if img_url: st.image(img_url)
        
        # Memory Save
        msg_data = {"role": "assistant", "content": final_text}
        if img_url: msg_data["image"] = img_url
        st.session_state.messages.append(msg_data)
