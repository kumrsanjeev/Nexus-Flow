import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Check Secrets.")
        return None
        
    # FIX: No version string, just pure API key configuration
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    Role: Nexus Flow Pro. 
    Memory: Use history to remember Sanjeev's context.
    Style: Expert in Hinglish, Video Editing, and SAT/JEE.
    Image: Use [GENERATE_IMAGE: prompt] for visuals.
    """
    
    # PRO FIX: Model Scanning to bypass 404
    try:
        # Check all available models for your specific key
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Priority selection
        selected = None
        for target in ["models/gemini-1.5-flash", "models/gemini-pro"]:
            if target in available_models:
                selected = target
                break
        
        if not selected and available_models:
            selected = available_models[0]
            
        return genai.GenerativeModel(model_name=selected, system_instruction=instruction)
    except Exception:
        # Final fallback
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    if model is None: return "Agent Error."
    # strictly Gemini requires history in 'user' and 'model' parts format
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
