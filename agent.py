import streamlit as st
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from pypdf import PdfReader
import os

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Nexus Flow Pro: RAG Edition ⚡", layout="wide")

# Custom Dark Theme CSS
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .stChatMessage { border-radius: 15px; border: 1px solid #1E1E1E; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API KEY SETUP ---
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    st.error("⚠️ Sanjeev, API Key missing in Secrets!")
    st.stop()

# --- 3. RAG ENGINE ---
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

# --- 4. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🧠 Knowledge Base")
    uploaded_files = st.file_uploader("Upload SAT/Editing PDFs", type="pdf", accept_multiple_files=True)
    
    if uploaded_files and st.button("Train Nexus Flow"):
        with st.spinner("Learning from documents..."):
            st.session_state.vector_db = process_pdf(uploaded_files)
            st.success("I'm now smarter!")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 6. CHAT DISPLAY ---
st.title("Nexus Flow Pro 🤖")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 7. RESPONSE LOGIC ---
if prompt := st.chat_input("Ask anything"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🔍 Nexus Flow is Analyzing...", expanded=False) as status:
            try:
                if st.session_state.vector_db:
                    # RAG Mode with LangChain
                    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
                    qa_chain = RetrievalQA.from_chain_type(
                        llm=llm, 
                        chain_type="stuff",
                        retriever=st.session_state.vector_db.as_retriever()
                    )
                    res = qa_chain.invoke(prompt)
                    final_text = res["result"]
                else:
                    # Normal Gemini Mode
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    res = model.generate_content(prompt)
                    final_text = res.text
                
                status.update(label="✅ Response Generated!", state="complete")
            except Exception as e:
                final_text = f"Error: {str(e)}"
                status.update(label="❌ Error occurred", state="error")

        st.markdown(final_text)
        st.session_state.messages.append({"role": "assistant", "content": final_text})
        
