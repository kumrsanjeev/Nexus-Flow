import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import os
import time

# ---------------- PAGE ----------------
st.set_page_config(page_title="Nexus Flow Ultra AI 🤖", layout="wide")

# ---------------- API KEYS ----------------
GEMINI_KEY = st.secrets.get("GOOGLE_API_KEY")
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    os.environ["GOOGLE_API_KEY"] = GEMINI_KEY

openai_client = None
if OPENAI_KEY:
    openai_client = OpenAI(api_key=OPENAI_KEY)

# ---------------- MODEL LIST ----------------
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

OPENAI_MODEL = "gpt-4o-mini"

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

# ---------------- MULTI AI FUNCTION ----------------
def generate_response(prompt):
    
    # 🔥 1. TRY GEMINI FIRST
    if GEMINI_KEY:
        for model_name in GEMINI_MODELS:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text, f"Gemini ({model_name})"

            except Exception as e:
                error = str(e)

                # quota → try next system
                if "429" in error or "quota" in error.lower():
                    break

                if "404" in error:
                    continue

    # 🔥 2. FALLBACK TO OPENAI
    if openai_client:
        try:
            res = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            return res.choices[0].message.content, f"OpenAI ({OPENAI_MODEL})"

        except Exception as e:
            return f"❌ OpenAI Error: {str(e)}", "openai_error"

    # 🔥 3. FINAL FAIL
    return "❌ All AI services failed.\n\n👉 Check API keys or billing.", "none"

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
st.title("🤖 Nexus Flow Ultra AI")
st.caption("Gemini + OpenAI Auto Switching AI")

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
Use this context to answer:

{context}

Question: {prompt}
"""
                else:
                    final_prompt = prompt

                response, model_used = generate_response(final_prompt)

            except Exception as e:
                response = f"❌ Error: {str(e)}"
                model_used = "error"

        st.markdown(response)
        st.caption(f"⚙️ Model used: {model_used}")

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })
