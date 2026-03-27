import google.generativeai as genai
import streamlit as st

def initialize_agent():
    # Fetch API key from Streamlit secrets
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key not found in Streamlit Secrets!")
        return None
        
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # Try using this specific string which is most compatible
    model = genai.GenerativeModel("models/gemini-1.5-flash") 
    return model

def get_chat_response(model, user_input, history):
    if model is None:
        return "Model not initialized. Check API Key."
        
    # Start chat with reformatted history
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
