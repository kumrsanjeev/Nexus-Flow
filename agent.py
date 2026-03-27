import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        return None
    
    # Configure with stable settings
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # PRO FIX: Let the library pick the best available model
    # No prefixes, no version strings
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model
    except:
        try:
            model = genai.GenerativeModel("gemini-pro")
            return model
        except:
            return None

def get_chat_response(model, user_input, history):
    if not model: return "System Error: Model not initialized."
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
