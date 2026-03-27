import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing in Secrets!")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Stable instructions
    instruction = "You are Nexus Flow Pro. Expert in Video Editing and SAT/JEE."
    
    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=instruction)
        return model
    except:
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, api_history):
    if model is None: return "Agent not initialized."
    try:
        # FIX: Using 'history' instead of 'messages' to fix TypeError
        chat = model.start_chat(history=api_history)
        response = chat.send_message(user_input)
        return response.text
    except Exception as e:
        if "429" in str(e):
            return "⚠️ Quota Full! 60 seconds wait karein."
        return f"API Error: {str(e)}"
