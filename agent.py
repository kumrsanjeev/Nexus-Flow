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
st.set_page_config(page_title="Nexus Flow Pro: RAG Edition ⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .thinking-box { background-color: #1a1c23; border-left: 4px solid #00ffcc; padding: 10px; margin: 10px 0; color: #00ffcc; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API KEY ---
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    st.error("⚠️ Sanjeev, API Key missing in Secrets!")
    st.stop()

# --- 3. RAG ENGINE (Data Processing) ---
def process_pdf(pdf_files):
    text = ""
    for pdf in pdf_files:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    
    # Split text into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)
    
    # Create Vector Store
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_db = FAISS.from_texts(chunks, embeddings)
    return vector_db

# --- 4. SYSTEM INSTRUCTION ---
instruction = "You are Nexus Flow Pro, Sanjeev's AI Avatar. Use the provided context to answer questions accurately. If no context is provided, use your general knowledge. Speak in Hinglish."

# --- 5. SIDEBAR (Knowledge Management) ---
with st.sidebar:
    st.title("🧠 Knowledge Base")
    uploaded_files = st.file_uploader("Upload SAT/Editing PDFs", type="pdf", accept_multiple_files=True)
    
    if uploaded_files:
        with st.spinner("Learning from documents..."):
            st.session_state.vector_db = process_pdf(uploaded_files)
            st.success("Documents Learned!")

    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 6. CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 7. REASONING & RESPONSE ---
if prompt := st.chat_input("Sanjeev, kya puchna hai?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🔍 Nexus Flow is Analyzing...", expanded=True) as status:
            try:
                # If documents are uploaded, use RAG
                if "vector_db" in st.session_state:
                    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
                    qa_chain = RetrievalQA.from_chain_type(
                        llm=llm, retriever=st.session_state.vector_db.as_retriever()
                    )
                    res = qa_chain.invoke(prompt)
                    final_text = res["result"]
                else:
                    # Normal Chat
                    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=instruction)
                    res = model.generate_content(prompt)
                    final_text = res.text

                status.update(label="✅ Knowledge Retrieved!", state="complete", expanded=False)
            except Exception as e:
                final_text = f"Error: {str(e)}"

        st.markdown(final_text)
        st.session_state.messages.append({"role": "assistant", "content": final_text})
        
