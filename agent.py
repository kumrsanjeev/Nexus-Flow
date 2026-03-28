import streamlit as st
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from pypdf import PdfReader
import os

# PAGE SETUP
st.set_page_config(page_title="Nexus Flow Pro 🤖", layout="wide")

# API KEY
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    st.error("⚠️ API Key missing! Check Secrets.")
    st.stop()

# PDF PROCESS
def process_pdf(pdf_files):
    text = ""
    for pdf in pdf_files:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_db = FAISS.from_texts(chunks, embeddings)

    return vector_db

# SESSION
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None

# SIDEBAR
with st.sidebar:
    st.title("📂 Knowledge Base")
    uploaded_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)

    if uploaded_files and st.button("Sync Documents"):
        with st.spinner("Learning..."):
            st.session_state.vector_db = process_pdf(uploaded_files)
            st.success("Documents Synced!")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# MAIN UI
st.title("Nexus Flow Pro 🤖")
st.caption("AI + PDF Memory (RAG)")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# CHAT
if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                if st.session_state.vector_db:
                    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

                    qa_chain = RetrievalQA.from_chain_type(
                        llm=llm,
                        chain_type="stuff",
                        retriever=st.session_state.vector_db.as_retriever()
                    )

                    res = qa_chain.invoke({"query": prompt})
                    final_text = res["result"]

                else:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    res = model.generate_content(prompt)
                    final_text = res.text

            except Exception as e:
                final_text = f"❌ Error: {str(e)}"

        st.markdown(final_text)
        st.session_state.messages.append({"role": "assistant", "content":
