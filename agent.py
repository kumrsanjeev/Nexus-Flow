import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        return None
    
    # FIX: Config mein koi version mat likho
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Direct model call
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model
    except:
        return genai.GenerativeModel("gemini-pro")

def get_chat_response(model, user_input, history):
    if not model: return "Model Error"
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
