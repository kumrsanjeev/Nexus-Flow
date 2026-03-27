# app.py
import streamlit as st
import google.generativeai as genai

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="Nexus Flow Pro")

# ----------------- SESSION STATE -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory" not in st.session_state:
    st.session_state.memory = []

# ----------------- MODEL INITIALIZATION -----------------
def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Google API key st.secrets me nahi hai!")
        return None

    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    try:
        available_models = [m.name for m in genai.list_models()]
    except Exception as e:
        st.error(f"Error listing models: {e}")
        return None
    
    preferred_model = "gemini-1.5"
    if preferred_model in available_models:
        model_name = preferred_model
    elif available_models:
        model_name = available_models[0]
    else:
        st.error("Koi model available nahi hai! Check account access.")
        return None
    
    return genai.GenerativeModel(model_name)

# ----------------- CHAT FUNCTION -----------------
def get_chat_response(model, user_input, history):
    if not model:
        return "Model Error"
    
    # Convert history to API compatible format
    api_history = []
    for msg in history:
        if "author" in msg and "content" in msg:
            api_history.append({"author": msg["author"], "content": msg["content"]})
    
    chat = model.start_chat(messages=api_history)
    response = chat.send_message(user_input)
    return response.text

# ----------------- STREAMLIT UI -----------------
st.title("Nexus Flow Pro Chatbot")

# Display previous messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])

# Chat input
if prompt := st.chat_input("Puchiye Sanjeev..."):
    # Save user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.memory.append({"author": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        model = initialize_agent()
        if model:
            res = get_chat_response(model, prompt, st.session_state.memory)
            st.write(res)
            
            # Save assistant message
            st.session_state.messages.append({"role": "assistant", "content": res})
            st.session_state.memory.append({"author": "assistant", "content": res})
        else:
            st.error("Model initialization failed! Check API key and access.")
