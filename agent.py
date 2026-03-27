import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Check Streamlit Secrets.")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    You are Nexus Flow AI, Sanjeev's personal partner.
    1. MEMORY: Always remember previous context. You are smart like Gemini/ChatGPT.
    2. IMAGE: Respond ONLY with [GENERATE_IMAGE: descriptive prompt] for image requests.
    3. STYLE: Use natural Hinglish. Expert in Video Editing & Coding.
    """
    
    # --- FIX FOR 404 ERROR ---
    try:
        # Check for available models to avoid 404
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Priority logic
        selected = None
        for target in ["models/gemini-1.5-flash", "models/gemini-pro", "gemini-1.5-flash"]:
            if target in available:
                selected = target
                break
        
        if not selected and available:
            selected = available[0]
            
        return genai.GenerativeModel(model_name=selected, system_instruction=instruction)
    except:
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, chat_history):
    # GEMINI MEMORY FORMATTING
    # chat_history: list of {'role': 'user/model', 'parts': [text]}
    chat = model.start_chat(history=chat_history)
    response = chat.send_message(user_input)
    return response.text
    
