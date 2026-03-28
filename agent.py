import streamlit as st
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from pypdf import PdfReader
import os

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Nexus Flow Pro 🤖", layout="wide")

# --- 2. API KEY SETUP ---
# Settings > Secrets mein GOOGLE_API_KEY hona zaroori hai
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    st.error("⚠️ API Key missing! Check Secrets.")
    st.stop()

# --- 3. RAG CORE FUNCTIONS ---
def process_pdf(pdf_files):
    text = ""
    for pdf in pdf_files:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    
    # Text ko small chunks mein divide karna (RAG Process)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)
    
    # Google Embeddings model ka use karna
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_db = FAISS.from_texts(chunks, embeddings)
    return vector_db

# --- 4. SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None

# --- 5. SIDEBAR (The Knowledge Center) ---
with st.sidebar:
    st.title("📂 Knowledge Base")
    uploaded_files = st.file_uploader("Upload PDFs (SAT/Code/Notes)", type="pdf", accept_multiple_files=True)
    
    if uploaded_files and st.button("Sync Documents"):
        with st.spinner("Learning..."):
            st.session_state.vector_db = process_pdf(uploaded_files)
            st.success("Documents Synced!")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 6. MAIN UI ---
st.title("Nexus Flow Pro 🤖")
st.caption("Advanced Generic AI with PDF Memory")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 7. SMART CHAT LOGIC ---
if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🔍 Nexus Flow is Analyzing...", expanded=False) as status:
            try:
                if st.session_state.vector_db:
                    # RAG MODE: Documents se answer dhundna
                    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
                    qa_chain = RetrievalQA.from_chain_type(
                        llm=llm, 
                        chain_type="stuff",
                        retriever=st.session_state.vector_db.as_retriever()
                    )
                    res = qa_chain.invoke(prompt)
                    final_text = res["result"]
                else:
                    # GENERAL MODE: Gemini 1.5 Flash ka gyan
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    res = model.generate_content(prompt)
                    final_text = res.text
                
                status.update(label="✅ Analysis Done!", state="complete")
            except Exception as e:
                final_text = f"❌ Error: {str(e)}"
                status.update(label="Critical Error", state="error")

        st.markdown(final_text)
        st.session_state.messages.append({"role": "assistant", "content": final_text})
        
