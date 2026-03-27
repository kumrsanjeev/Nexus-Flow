import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        return None
    
    # Configure without specifying a version
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    try:
        # Best way to avoid 404: Let the library pick the model name directly
        model = genai.GenerativeModel('gemini-1.5-flash') 
        return model
    except Exception:
        # Fallback if flash is not available
        return genai.GenerativeModel('gemini-pro')

def get_chat_response(model, user_input, history):
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
