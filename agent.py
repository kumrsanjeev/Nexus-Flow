import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        return None
    
    # Simple configuration - let the library handle the endpoint
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Hard-coded stable names
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model
    except:
        return genai.GenerativeModel("gemini-pro")

def get_chat_response(model, user_input, history):
    if not model: return "Agent not initialized."
    try:
        chat = model.start_chat(history=history)
        response = chat.send_message(user_input)
        return response.text
    except Exception as e:
        if "429" in str(e):
            return "⚠️ Quota Full: Please wait 60 seconds."
        return f"Error: {str(e)}"
        
