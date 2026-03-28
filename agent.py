import streamlit as st
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from pypdf import PdfReader
import urllib.parse
import re
import os

# --- PAGE SETUP ---
st.set_page_config(page_title="Nexus Flow Pro 🤖", layout="wide")

# --- API SETUP ---
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    st.error("⚠️ API Key missing in Secrets!")
    st.stop()

# --- SYSTEM INSTRUCTION ---
instruction = """
You are Nexus Flow AI. 
1. IMAGE: For image requests, respond ONLY with: [GENERATE_IMAGE: descriptive prompt in English]
2. THINKING: Use <thinking> logic </thinking> for complex tasks.
3. PERSONALITY: Helpful Generic AI.
"""

# --- RAG ENGINE (PDF) ---
def process_pdf(pdf_files):
    text = ""
    for pdf in pdf_files:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text(text)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    return FAISS.from_texts(chunks, embeddings)

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("📂 Knowledge")
    uploaded = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("Sync"):
        st.session_state.vector_db = process_pdf(uploaded)
        st.success("Ready!")

# --- CHAT LOGIC ---
st.title("Nexus Flow Pro 🤖")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m: st.image(m["image"])

if prompt := st.chat_input("Kaise help karu?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Important Fix: Using gemini-1.5-flash for reliability
            if st.session_state.vector_db:
                llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
                qa = RetrievalQA.from_chain_type(llm=llm, retriever=st.session_state.vector_db.as_retriever())
                raw_res = qa.invoke(prompt)["result"]
            else:
                model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=instruction)
                raw_res = model.generate_content(prompt).text

            # Image & Thinking Logic
            final_text = raw_res
            img_url = None
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(img_prompt)}?nologo=true"
                    final_text = f"🎨 Generated: {img_prompt}"

            st.markdown(final_text)
            if img_url: st.image(img_url)
            
            msg = {"role": "assistant", "content": final_text}
            if img_url: msg["image"] = img_url
            st.session_state.messages.append(msg)
        except Exception as e:
            st.error(f"Error: {e}")
                
