import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing!")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    Role: Nexus Flow 'Universal' Pro.
    - Identity: Sanjeev's Digital Partner.
    - Thinking: Use <thinking> tags for reasoning.
    - Images: Respond ONLY with [GENERATE_IMAGE: descriptive prompt] for visuals.
    - Style: Professional Hinglish.
    """
    
    # --- PRO FIX: Try Multiple Model Name Formats ---
    # Kuch accounts mein 'models/gemini-pro' chalta hai, kuch mein sirf 'gemini-pro'
    test_models = ["gemini-1.5-flash", "models/gemini-1.5-flash", "gemini-pro", "models/gemini-pro"]
    
    selected_model = None
    for m_name in test_models:
        try:
            model = genai.GenerativeModel(model_name=m_name, system_instruction=instruction)
            # Chota sa check call
            selected_model = model
            break 
        except Exception:
            continue
            
    if not selected_model:
        # Last resort fallback
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)
        
    return selected_model

def get_chat_response(model, user_input, history):
    if model is None: return "Agent initialization failed."
    try:
        chat = model.start_chat(history=history)
        response = chat.send_message(user_input)
        return response.text
    except Exception as e:
        return f"API Error: {str(e)}"
        
