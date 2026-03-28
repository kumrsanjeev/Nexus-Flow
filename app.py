import streamlit as st
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re

# ---------------- PAGE ----------------
st.set_page_config(page_title="Offline AI 🤖", layout="wide")

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chunks" not in st.session_state:
    st.session_state.chunks = []

# ---------------- PDF PROCESS ----------------
def process_pdf(files):
    text = ""
    for file in files:
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_text(text)

    return chunks

# ---------------- SIMPLE SEARCH ----------------
def search_chunks(query, chunks):
    scores = []

    query_words = set(re.findall(r"\w+", query.lower()))

    for chunk in chunks:
        chunk_words = set(re.findall(r"\w+", chunk.lower()))
        score = len(query_words.intersection(chunk_words))
        scores.append((score, chunk))

    scores.sort(reverse=True, key=lambda x: x[0])

    return [chunk for score, chunk in scores[:3] if score > 0]

# ---------------- OFFLINE AI ----------------
def offline_ai(prompt, chunks):
    prompt_lower = prompt.lower()

    # 🔹 basic chat
    if "hello" in prompt_lower or "hi" in prompt_lower:
        return "Hello 👋 I'm your offline AI. Ask me anything!"

    if "who are you" in prompt_lower:
        return "I am a fully offline AI 🤖 running without any API."

    # 🔹 RAG mode
    if chunks:
        results = search_chunks(prompt, chunks)

        if results:
            context = "\n\n".join(results)

            return f"""
📄 Based on your document:

{context}

🧠 Answer:
This information suggests that your query is related to the above content.
"""

    # 🔹 fallback
    return "⚠️ I couldn't find relevant info.\n\nTry uploading a PDF or ask simpler question."

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("📂 Upload PDF")

    files = st.file_uploader("Upload", type="pdf", accept_multiple_files=True)

    if files and st.button("Process"):
        with st.spinner("Reading PDF..."):
            st.session_state.chunks = process_pdf(files)
        st.success("✅ PDF Ready!")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ---------------- UI ----------------
st.title("🤖 Offline AI (No API)")
st.caption("ChatGPT Style + Free RAG System")

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
            response = offline_ai(prompt, st.session_state.chunks)

        st.markdown(response)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })
