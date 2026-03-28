import streamlit as st
from agent import process_pdf, ask_question

st.set_page_config(page_title="PDF Chatbot")

st.title("📄 PDF Chatbot (RAG System)")

# Session
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None

# Upload PDF
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:
    with st.spinner("Processing PDF..."):
        qa_chain = process_pdf(uploaded_file, st.secrets["GOOGLE_API_KEY"])
        st.session_state.qa_chain = qa_chain
    st.success("✅ PDF Ready! Ask questions 👇")

# Ask question
query = st.text_input("Ask something from PDF")

if query and st.session_state.qa_chain:
    answer = ask_question(st.session_state.qa_chain, query)
    st.write(answer)
