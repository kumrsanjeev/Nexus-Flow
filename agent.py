import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        return None
    
    # Configure strictly with stable settings
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Instructions for Sanjeev's Bot
    instruction = "You are Nexus Flow Pro. Use [GENERATE_IMAGE: prompt] for images."
    
    try:
        # Use simple model name to avoid 404
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=instruction)
        return model
    except:
        return genai.GenerativeModel("gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
