import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        return None
    
    # Configure with NO version strings
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Try multiple variants - library will pick the right one
    for model_name in ["gemini-1.5-flash", "gemini-pro"]:
        try:
            return genai.GenerativeModel(model_name)
        except:
            continue
    return None

def get_chat_response(model, user_input, history):
    if not model: return "System Error."
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
