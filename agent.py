import google.generativeai as genai
import streamlit as st

def initialize_agent():
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    # Use "gemini-1.5-flash" - it is the most reliable version for 2026
    model = genai.GenerativeModel("gemini-1.5-flash") 
    return model

def get_chat_response(model, user_input, history):
    # Start a chat session with the reformatted history
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
