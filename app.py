import streamlit as st
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from pypdf import PdfReader
import urllib.parse
import re
import os

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Nexus Flow AI", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .thinking-box { background-color: #1a1c23; border-left: 4px solid #00ffcc; padding: 10px; margin: 10px 0; color: #00ffcc; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API KEY SETUP ---
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    st.error("⚠️ API Key missing! Add GOOGLE_API_KEY in Secrets.")
    st.stop()

# --- 3. CHATBOT ENGINE ---
def initialize_agent():
    instruction = """
    You are Nexus Flow AI. 
    1. IMAGE: For image requests, respond ONLY with: [GENERATE_IMAGE: descriptive prompt in English]
    2. THINKING: For complex tasks, use <thinking> logic </thinking> then final answer.
    3. LANGUAGE: Use Hinglish.
    """
    return genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=instruction)

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

# --- 4. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("📂 Knowledge Base")
    uploaded = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("Sync Documents"):
        with st.spinner("Learning..."):
            st.session_state.vector_db = process_pdf(uploaded)
            st.success("Docs Synced!")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- 6. MAIN CHAT UI ---
st.title("Nexus Flow AI 🤖")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m: st.image(m["image"])

if prompt := st.chat_input("Kaise help karu Sanjeev?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            if st.session_state.vector_db and any(x in prompt.lower() for x in ['pdf', 'file', 'doc']):
                llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
                qa = RetrievalQA.from_chain_type(llm=llm, retriever=st.session_state.vector_db.as_retriever())
                raw_res = qa.invoke(prompt)["result"]
            else:
                model = initialize_agent()
                raw_res = model.generate_content(prompt).text

            final_text = raw_res
            img_url = None

            # Thinking Parser
            if "<thinking>" in raw_res:
                parts = raw_res.split("</thinking>")
                thought = parts[0].replace("<thinking>", "").strip()
                final_text = parts[1].strip()
                st.markdown(f'<div class="thinking-box"><b>🧠 Logic:</b><br>{thought}</div>', unsafe_allow_html=True)

            # Image Parser
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(img_prompt)}?width=1024&height=1024&nologo=true"
                    final_text = f"🎨 **Image:** {img_prompt}"

            st.markdown(final_text)
            if img_url: st.image(img_url)
            
            msg = {"role": "assistant", "content": final_text}
            if img_url: msg["image"] = img_url
            st.session_state.messages.append(msg)
        except Exception as e:
            st.error(f"Error: {e}")
            
