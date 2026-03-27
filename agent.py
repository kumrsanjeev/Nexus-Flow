import google.generativeai as genai
import streamlit as st
import time

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        return None
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Try multiple models to see which one has quota left
    for m_name in ["gemini-1.5-flash", "gemini-pro"]:
        try:
            return genai.GenerativeModel(model_name=m_name)
        except:
            continue
    return None

def get_chat_response(model, user_input, history):
    try:
        chat = model.start_chat(history=history)
        response = chat.send_message(user_input)
        return response.text
    except Exception as e:
        if "429" in str(e):
            return "⚠️ QUOTA_FULL: Sanjeev, Google ki free limit khatam ho gayi hai. Please 60 seconds wait karke phir se try karein."
        return f"Error: {str(e)}"
        
