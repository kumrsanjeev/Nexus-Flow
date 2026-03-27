import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing in Secrets!")
        return None
        
    # FIX: No version strings, purely stable config
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    Role: Nexus Flow Pro. Sanjeev's digital partner.
    Context: Expert in Video Editing (CapCut), Coding (C++, Python), and SAT/JEE Prep.
    Style: Speak in Hinglish. Be helpful and smart.
    """
    
    try:
        # Use stable 1.5-flash for speed and reliability
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=instruction)
        return model
    except:
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, api_history):
    if model is None: return "Agent not initialized."
    try:
        # FIX: Using 'history' instead of 'messages' to avoid TypeError
        chat = model.start_chat(history=api_history)
        response = chat.send_message(user_input)
        return response.text
    except Exception as e:
        if "429" in str(e):
            return "⚠️ Quota Full! Sanjeev, 60 seconds wait karke try karein."
        return f"API Error: {str(e)}"
      
