import streamlit as st
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from pypdf import PdfReader
import os

# ---------------- PAGE SETUP ----------------
st.set_page_config(page_title="Nexus Flow Pro 🤖", layout="wide")

# ---------------- API KEY ----------------
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ API Key missing! Add in secrets.toml")
    st.stop()

genai.configure(api_key=api_key)
os.environ["GOOGLE_API_KEY"] = api_key

# ---------------- PDF PROCESS FUNCTION ----------------
def process_pdf(pdf_files):
    text = ""

    for pdf in pdf_files:
        reader = PdfReader(pdf)
        for page in reader.pages:
            text += page.extract_text() or ""

    # Split text
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_text(text)

    # Embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001"
    )

    # Vector DB
    vector_db = FAISS.from_texts(chunks, embeddings)

    return vector_db

# ---------------- SESSION STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "vector_db" not in st.session_state:
    st.session_state.vector_db = None

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("📂 Knowledge Base")

    uploaded_files = st.file_uploader(
        "Upload PDFs",
        type="pdf",
        accept_multiple_files=True
    )

    if uploaded_files and st.button("Sync Documents"):
        with st.spinner("Processing PDFs..."):
            st.session_state.vector_db = process_pdf(uploaded_files)
        st.success("✅ Documents Ready!")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ---------------- MAIN UI ----------------
st.title("🤖 Nexus Flow Pro")
st.caption("Chat with AI + Your PDFs (RAG System)")

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- CHAT INPUT ----------------
prompt = st.chat_input("Ask me anything...")

if prompt:
    # User message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant reply
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # RAG MODE
                if st.session_state.vector_db:
                    llm = ChatGoogleGenerativeAI(
                        model="gemini-1.5-flash"
                    )

                    qa_chain = RetrievalQA.from_chain_type(
                        llm=llm,
                        chain_type="stuff",
                        retriever=st.session_state.vector_db.as_retriever()
                    )

                    result = qa_chain.invoke({"query": prompt})
                    final_text = result["result"]

                # NORMAL CHAT
                else:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response = model.generate_content(prompt)
                    final_text = response.text

            except Exception as e:
                final_text = f"❌ Error: {str(e)}"

        st.markdown(final_text)

        # ✅ FIXED (NO SYNTAX ERROR)
        st.session_state.messages.append({
            "role": "assistant",
            "content": final_text
        })
