import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re

# --- 1. INITIALIZE CLIENTS ---
def initialize_clients():
    groq_key = st.secrets.get("GROQ_API_KEY")
    google_key = st.secrets.get("GOOGLE_API_KEY")
    
    if not groq_key or not google_key:
        st.error("⚠️ API Keys missing! Add GROQ_API_KEY and GOOGLE_API_KEY in Secrets.")
        return None, None
    
    groq_client = Groq(api_key=groq_key)
    genai.configure(api_key=google_key)
    return groq_client, genai

# --- 2. KNOWLEDGE RETRIEVAL (PDF Logic) ---
def process_pdf_to_faiss(pdf_files):
    text = ""
    for pdf in pdf_files:
        reader = PdfReader(pdf)
        for page in reader.pages:
            text += page.extract_text() or ""
    
    # Text Chunks (Sanjeev, hum chunks chote rakhenge fast processing ke liye)
    chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
    
    # Google Embeddings (High Limit - No Error)
    embeddings = [genai.embed_content(model="models/embedding-001", 
                                     content=c, 
                                     task_type="retrieval_document")['embedding'] for c in chunks]
    
    index = faiss.IndexFlatL2(len(embeddings[0]))
    index.add(np.array(embeddings).astype('float32'))
    return index, chunks

# --- 3. CORE CHAT LOGIC ---
def get_nexus_response(prompt, context_index=None, chunks=None):
    groq_client, _ = initialize_clients()
    
    # PDF Context Search
    context_text = ""
    if context_index and chunks:
        q_emb = genai.embed_content(model="models/embedding-001", 
                                    content=prompt, 
                                    task_type="retrieval_query")['embedding']
        D, I = context_index.search(np.array([q_emb]).astype('float32'), k=3)
        context_text = "\n".join([chunks[i] for i in I[0] if i < len(chunks)])

    # Nexus System Prompt
    system_msg = """
    You are Nexus Flow Ultra.
    1. LOGIC: Use <thinking> tags for complex math/coding.
    2. IMAGES: Use [GENERATE_IMAGE: prompt] for visuals.
    3. STYLE: Professional Hinglish.
    """

    # Groq API Call (Llama 3 70B - Super Fast)
    completion = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": f"Context: {context_text}\n\nUser: {prompt}"}
        ],
        temperature=0.6
    )
    return completion.choices[0].message.content

# --- 4. RESPONSE PARSER (For Images & Thinking) ---
def parse_nexus_output(raw_text):
    final_text = raw_text
    img_url = None
    thought = None

    # Extract Thinking
    if "<thinking>" in raw_text:
        parts = raw_text.split("</thinking>")
        thought = parts[0].replace("<thinking>", "").strip()
        final_text = parts[1].strip()

    # Extract Image Prompt
    if "[GENERATE_IMAGE:" in final_text:
        match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
        if match:
            prompt_str = match.group(1).strip()
            encoded = urllib.parse.quote(prompt_str)
            img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"
            final_text = f"🎨 **Nexus Visualizer:** {prompt_str}"

    return final_text, img_url, thought
    
