import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Check Streamlit Secrets.")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    You are Nexus Flow AI. 
    1. Always think step-by-step inside <thinking> tags.
    2. For images, use ONLY: [GENERATE_IMAGE: descriptive prompt]
    3. You are Sanjeev's partner. Be smart and Hinglish.
    """
    
    # --- The "No-Fail" Model List ---
    model_options = [
        "gemini-1.5-flash", 
        "models/gemini-1.5-flash", 
        "gemini-pro", 
        "models/gemini-pro"
    ]
    
    for m_name in model_options:
        try:
            model = genai.GenerativeModel(model_name=m_name, system_instruction=instruction)
            # Chota sa test call check karne ke liye ki model active hai ya nahi
            return model
        except Exception:
            continue
            
    return None

def get_chat_response(model, user_input, history):
    if model is None: return "Error: Model initialization failed."
    try:
        chat = model.start_chat(history=history)
        response = chat.send_message(user_input)
        return response.text
    except Exception as e:
        return f"API Error: {str(e)}"
        
