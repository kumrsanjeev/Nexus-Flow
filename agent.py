import google.generativeai as genai
import streamlit as st

def initialize_agent():
    # API Key check
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Add it to Streamlit Secrets.")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Using the most compatible string for 2026
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    return model

def get_chat_response(model, user_input, history):
    # Gemini expects history in a specific 'user'/'model' format
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
