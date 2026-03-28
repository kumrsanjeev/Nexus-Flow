import streamlit as st
from groq import Groq
import google.generativeai as genai
import requests
import io
from PIL import Image
import re
import random
import time

# --- 1. PREMIUM GEMINI/CHATGPT UI THEME ---
st.set_page_config(page_title="Nexus Flow Ultra v31", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
    /* Gemini White Theme */
    .stApp { background-color: #ffffff; color: #1f1f1f; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #f0f4f9 !important; border-right: none; }
    [data-testid="stSidebar"] .stButton>button { background-color: #f0f4f9 !important; color: #1a73e8 !important; border-radius: 20px; border: 1px solid #c4c7c5; }
    
    /* Gemini style message bubbles */
    .stChatMessage { background-color: transparent !important; border: none !important; padding: 10px 0 !important; }
    
    /* Thinking box (Logic) */
    .thinking-box {
        background-color: #f0f7ff;
        border-radius: 12px;
        padding: 15px;
        color: #0056b3;
        font-size: 0.9rem;
        border-left: 5px solid #0056b3;
        margin-bottom: 10px;
    }

    /* Suggested Buttons (Pills) */
    .stButton>button {
        background-color: #ffffff;
        color: #444746 !important;
        border: 1px solid #c4c7c5 !important;
        border-radius: 25px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #f1f3f4 !important; border-color: #1a73e8 !important; }

    /* Chat Input Styling */
    .stChatInputContainer { padding-bottom: 2rem; }
    .stChatInput { border-radius: 26px !important; border: 1px solid #e5e7eb !important; background-color: #f0f4f9 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. KEYS & INITIALIZATION (Secure Mode) ---
groq_key = st.secrets.get("GROQ_API_KEY")
google_key = st.secrets.get("GOOGLE_API_KEY")
hf_token = st.secrets.get("HF_TOKEN")

if not groq_key or not google_key or not hf_token:
    st.error("Missing API Keys (Groq, Google, or HF_TOKEN) in Streamlit Secrets!")
    st.stop()

# Clients Initialization
groq_client = Groq(api_key=groq_key)
genai.configure(api_key=google_key)

# Hugging Face Configuration (Using Stable Diffusion XL)
HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HF_HEADERS = {"Authorization": f"Bearer {hf_token}"}

if "messages" not in st.session_state: st.session_state.messages = []
if "db" not in st.session_state: st.session_state.db = None

# --- 3. SIDEBAR (Nexus Hub) ---
with st.sidebar:
    st.markdown("<h3 style='color:#1a73e8; text-align:center;'>Nexus Core ⚡</h3>", unsafe_allow_html=True)
    if st.button("➕ New Deep Chat"):
        st.session_state.messages = []
        st.session_state.db = None
        st.rerun()
    st.markdown("---")
    uploaded = st.file_uploader("Upload PDFs for Analysis", type="pdf", accept_multiple_files=True)
    if uploaded and st.button("🚀 Sync Brain"):
        text = ""
        for f in uploaded:
            reader = PdfReader(f)
            for page in reader.pages: text += page.extract_text() or ""
        chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
        embeddings = [genai.embed_content(model="models/embedding-001", content=c, task_type="retrieval_document")['embedding'] for c in chunks]
        index = faiss.IndexFlatL2(len(embeddings[0]))
        index.add(np.array(embeddings).astype('float32'))
        st.session_state.db, st.session_state.chunks = index, chunks
        st.success("Brain Synced! ✅")

# --- 4. HUGGING FACE IMAGE ENGINE (Stable & High Quality) ---
def generate_hf_image(prompt):
    """Wait and fetch image from Hugging Face"""
    payload = {"inputs": prompt, "options": {"wait_for_model": True}}
    try:
        response = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload, timeout=60)
        
        if response.status_code == 200:
            image_bytes = response.content
            image = Image.open(io.BytesIO(image_bytes))
            return image
        
        elif response.status_code == 503:
            st.warning("⏳ Hugging Face model is warming up... waiting 10 seconds.")
            time.sleep(10)
            return generate_hf_image(prompt) # Retry after sleep
        
        else:
            st.error(f"🚨 Image Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"🚨 Image Engine Crash: {e}")
        return None

# --- 5. CHAT DISPLAY ---
# Displaying Home Suggestions if empty
if not st.session_state.messages:
    st.markdown("<h1 style='color:#1f1f1f; font-weight:500; font-size:3rem; margin-top:80px;'>Hi Sanjeev</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#c4c7c5; font-size:2.8rem; font-weight:500; margin-bottom:50px;'>Where should we start?</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🖼️ **Create:** A high-quality image of a cyberpunk city"):
            st.session_state.messages.append({"role":"user", "content":"Create a realistic cyberpunk city image"})
            st.rerun()
        if st.button("📝 **Write:** Hinglish essay on Future of AI"):
            st.session_state.messages.append({"role":"user", "content":"Future of AI par ek detailed Hinglish essay likho"})
            st.rerun()
    with col2:
        if st.button("💻 **Code:** Python logic for basic calculator"):
            st.session_state.messages.append({"role":"user", "content":"Python main calculator ka simple code aur logic samjhao"})
            st.rerun()
        if st.button("🧠 **Logic:** Deep Hinglish explanation of black holes"):
            st.session_state.messages.append({"role":"user", "content":"Black holes kaise bante hain deeply samjhao"})
            st.rerun()
else:
    # Display message history
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "image" in m and m["image"]:
                st.image(m["image"], use_container_width=True, caption="Generated by Nexus HF Engine")

# --- 6. CORE CHAT ENGINE (With ChatGPT Persona) ---
if prompt := st.chat_input("Message Nexus..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # Context retrieval
            context = ""
            if st.session_state.db:
                q_emb = genai.embed_content(model="models/embedding-001", content=prompt, task_type="retrieval_query")['embedding']
                D, I = st.session_state.db.search(np.array([q_emb]).astype('float32'), k=3)
                context = "\n".join([st.session_state.chunks[idx] for idx in I[0]])

            # MANDATORY CHATGPT PERSONA SYSTEM PROMPT
            sys_msg = f"""
            You are Nexus Flow Ultra, a deep reasoning AI model trained to behave exactly like ChatGPT-4.
            - PERSONA: Be friendly, extremely knowledgeable, and professional. Use emojis (🚀, ✨, 🧠) frequently but naturally.
            - FORMATTING: Answer like ChatGPT. Use bold headings, bullet points, numbered lists, and code blocks for readability.
            - LOGIC: For complex questions, use `<thinking> detailed step-by-step logic </thinking>` to explain your reasoning first.
            - LANGUAGE: Match the user's language (Hinglish/Hindi/English) and maintain a natural flow.
            - IMAGES: If asked for an image, reply ONLY with this exact format: [GENERATE_IMAGE: descriptive English prompt]. Never say "I can't generate".
            Context: {context}
            """
            
            # Streaming completion from Groq
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-8:]],
                stream=True,
                temperature=0.7 # For a mix of reasoning and creativity
            )

            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            # --- PARSING FOR DEEP REASONING & VISUALS ---
            final_text = full_response
            image_obj = None

            # 1. Thinking Logic Box
            if "<thinking>" in full_response:
                parts = full_response.split("</thinking>")
                thought = parts[0].replace("<thinking>","").strip()
                # Show reasoning like Gemini
                st.markdown(f'<div class="thinking-box">🔍 <b>Thinking Process:</b><br>{thought}</div>', unsafe_allow_html=True)
                final_text = parts[-1].strip()

            # 2. IMAGE GENERATION ENGINE (Hugging Face)
            if "[GENERATE_IMAGE:" in final_text:
                match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', final_text)
                if match:
                    img_prompt = match.group(1).strip()
                    with st.spinner("⏳ *Creating Premium Image...*"):
                        # Direct image bytes fetch
                        image_obj = generate_hf_image(img_prompt)
                    
                    # Clean final text completely of the tag
                    final_text = re.sub(r'\[GENERATE_IMAGE:.*?\]', '', final_text).strip()
                    if not final_text: final_text = f"🎨 **Generated your premium image:**"

            # Final Output display
            response_placeholder.markdown(final_text)
            if image_obj: 
                st.image(image_obj, use_container_width=True)
            
            st.session_state.messages.append({"role": "assistant", "content": final_text, "image": image_obj})

        except Exception as e:
            st.error(f"Nexus Sync Error: {e}")
        
