import streamlit as st
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import os

# ---------------- PAGE ----------------
st.set_page_config(page_title="Nexus Flow Ultimate 🤖", layout="wide")

# ---------------- API KEY ----------------
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ Add GOOGLE_API_KEY in secrets.toml")
    st.stop()

genai.configure(api_key=api_key)
os.environ["GOOGLE_API_KEY"] = api_key

# ---------------- PDF PROCESS ----------------
def process_pdf(files):
    text = ""

    for file in files:
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_text(text)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001"
    )

    vector_db = FAISS.from_texts(chunks, embeddings)

    return vector_db

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "vector_db" not in st.session_state:
    st.session_state.vector_db = None

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("📂 Upload PDFs")

    files = st.file_uploader("Upload PDF", type="pdf", accept_multiple_files=True)

    if files and st.button("Process"):
        with st.spinner("Processing PDFs..."):
            st.session_state.vector_db = process_pdf(files)
        st.success("✅ PDFs Ready!")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ---------------- MAIN UI ----------------
st.title("🤖 Nexus Flow Ultimate")
st.caption("AI + PDF Chat (RAG System)")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- CHAT ----------------
prompt = st.chat_input("Ask anything...")

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # 🔍 RAG MODE
                if st.session_state.vector_db:
                    docs = st.session_state.vector_db.similarity_search(prompt, k=3)

                    context = "\n\n".join([doc.page_content for doc in docs])

                    final_prompt = f"""
Answer the question using the context below.

Context:
{context}

Question:
{prompt}
"""

                else:
                    final_prompt = prompt

                # ✅ FIXED MODEL (WORKING)
                model = genai.GenerativeModel("gemini-pro")
                response = model.generate_content(final_prompt)

                final_text = response.text

            except Exception as e:
                final_text = f"❌ Error: {str(e)}"

        st.markdown(final_text)

        st.session_state.messages.append({
            "role": "assistant",
            "content": final_text
        })
