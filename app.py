import streamlit as st
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from pypdf import PdfReader
import os

# 1. Configuration
st.set_page_config(page_title="Nexus Flow Pro: Gemini Edition ⚡", layout="wide")

# 2. Key Handling (OpenAI hatakar Gemini set kiya)
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ Sanjeev, Secrets mein GOOGLE_API_KEY add karo!")
    st.stop()

# 3. RAG Functions (Using Google Embeddings)
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_vector_store(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    # Google specific embeddings
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    return vector_store

# 4. UI & Chat Logic
st.title("Nexus Flow Pro 🤖")

with st.sidebar:
    st.header("Study Material")
    pdf_docs = st.file_uploader("Upload SAT PDFs", accept_multiple_files=True)
    if st.button("Train Nexus Flow"):
        with st.spinner("Learning..."):
            raw_text = get_pdf_text(pdf_docs)
            st.session_state.vector_store = get_vector_store(raw_text)
            st.success("I'm now smarter!")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Puchiye Sanjeev..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if "vector_store" in st.session_state:
            # RAG Mode
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
            chain = RetrievalQA.from_chain_type(
                llm=llm, chain_type="stuff", 
                retriever=st.session_state.vector_store.as_retriever()
            )
            response = chain.invoke(prompt)["result"]
        else:
            # General Chat Mode
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt).text
        
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        
