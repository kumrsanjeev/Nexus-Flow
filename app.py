
import streamlit as st
from groq import Groq
import google.generativeai as genai
from pypdf import PdfReader
import faiss
import numpy as np
import urllib.parse
import re
import random

# --- UI ---
st.set_page_config(page_title="Nexus Flow Ultra", page_icon="✨", layout="wide")

# --- API KEYS ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")

if not groq_key or not google_key:
    st.error("API Keys missing!")
    st.stop()

client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# --- MEMORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "db" not in st.session_state:
    st.session_state.db = None

# --- SIDEBAR ---
with st.sidebar:
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()

    uploaded = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)

    if uploaded and st.button("🚀 Sync Knowledge"):
        text = ""
        for f in uploaded:
            reader = PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""

        chunks = [text[i:i+1000] for i in range(0, len(text), 800)]

        embeddings = [
            genai.embed_content(
                model="models/embedding-001",
                content=c,
                task_type="retrieval_document"
            )['embedding'] for c in chunks
        ]

        index = faiss.IndexFlatL2(len(embeddings[0]))
        index.add(np.array(embeddings).astype('float32'))

        st.session_state.db = index
        st.session_state.chunks = chunks
        st.success("Brain Synced!")

# --- CHAT DISPLAY ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image" in m and m["image"]:
            st.image(m["image"], use_container_width=True)

# --- CHAT INPUT ---
if prompt := st.chat_input("Ask Nexus..."):

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            # --- CONTEXT ---
            context = ""
            if st.session_state.db:
                q_emb = genai.embed_content(
                    model="models/embedding-001",
                    content=prompt,
                    task_type="retrieval_query"
                )['embedding']

                D, I = st.session_state.db.search(
                    np.array([q_emb]).astype('float32'), k=3
                )

                context = "\n".join(
                    [st.session_state.chunks[idx] for idx in I[0]]
                )

            # --- FORCE IMAGE DETECTION ---
            image_keywords = ["image", "photo", "draw", "picture", "generate", "pic"]
            if any(word in prompt.lower() for word in image_keywords):
                prompt += "\nRespond ONLY with [GENERATE_IMAGE: detailed prompt]"

            # --- SYSTEM PROMPT ---
            sys_msg = f"""
You are Nexus Flow Ultra.

🔥 LANGUAGE RULE (STRICT):
- Detect user's LAST message language
- Reply ONLY in that language
- No mixing languages
- Switch instantly if user switches

🔥 IMAGE RULE:
- If image needed → respond ONLY:
  [GENERATE_IMAGE: detailed English prompt]

🔥 STYLE:
- Smart like ChatGPT + Gemini
- Clean, helpful answers

Context:
{context}
"""

            chat_hist = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[-10:]
            ]

            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + chat_hist,
                stream=True
            )

            # --- STREAM FIX ---
            for chunk in completion:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    full_response += delta.content
                    response_placeholder.markdown(full_response + "▌")

            # --- IMAGE PARSER ---
            final_text = full_response.strip()
            img_url = None

            pattern = r'\[GENERATE_IMAGE:\s*(.*?)\]'
            match = re.search(pattern, full_response, re.IGNORECASE)

            if match:
                img_prompt = match.group(1).strip()

                enhanced_prompt = f"ultra realistic, 4k, high detail, {img_prompt}"
                encoded = urllib.parse.quote(enhanced_prompt)

                img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&seed={random.randint(1,999999)}"

                final_text = re.sub(pattern, '', full_response).strip()

            # --- OUTPUT ---
            response_placeholder.markdown(final_text)

            if img_url:
                st.image(img_url, use_container_width=True)

            st.session_state.messages.append({
                "role": "assistant",
                "content": final_text,
                "image": img_url
            })

        except Exception as e:
            st.error(f"Error: {e}")
