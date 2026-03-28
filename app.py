import streamlit as st
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import os
import time

# ---------------- PAGE ----------------
st.set_page_config(page_title="Nexus Flow Auto AI 🤖", layout="wide")

# ---------------- API ----------------
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ Add GOOGLE_API_KEY in secrets.toml")
    st.stop()

genai.configure(api_key=api_key)
os.environ["GOOGLE_API_KEY"] = api_key

# ---------------- SMART MODEL LIST ----------------
MODEL_LIST = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

# ---------------- PDF PROCESS ----------------
def process_pdf(files):
    text = ""
    for file in files:
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)

    embeddings = GoogleGenerativeAIEmbeddings(model="embedding-001")
    return FAISS.from_texts(chunks, embeddings)

# ---------------- SMART RESPONSE FUNCTION ----------------
def generate_with_fallback(prompt):
    for model_name in MODEL_LIST:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text, model_name
        except Exception as e:
            error = str(e)

            # quota error → wait and retry next
            if "429" in error:
                time.sleep(5)
                continue

            # model not found → try next
            if "404" in error:
                continue

            # other error
            continue

    return "❌ All models failed. Try again later.", "none"

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
        with st.spinner("Processing..."):
            st.session_state.vector_db = process_pdf(files)
        st.success("✅ Done!")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ---------------- UI ----------------
st.title("🤖 Nexus Flow Auto AI")
st.caption("Auto Model Switching + RAG System")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- CHAT ----------------
prompt = st.chat_input("Ask anything...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                if st.session_state.vector_db:
                    docs = st.session_state.vector_db.similarity_search(prompt, k=3)
                    context = "\n\n".join([doc.page_content for doc in docs])

                    final_prompt = f"""
Use the context below to answer:

{context}

Question: {prompt}
"""
                else:
                    final_prompt = prompt

                # 🔥 SMART MODEL SWITCH
                final_text, used_model = generate_with_fallback(final_prompt)

            except Exception as e:
                final_text = f"❌ Error: {str(e)}"
                used_model = "error"

        st.markdown(final_text)
        st.caption(f"⚙️ Model used: {used_model}")

        st.session_state.messages.append({
            "role": "assistant",
            "content": final_text
        })
