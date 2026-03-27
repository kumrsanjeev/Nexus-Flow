import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Check Secrets.")
        return None
        
    # Configure with default stable endpoint
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    Role: Nexus Flow Pro. 
    Memory: Persistent context history.
    Thinking: Analyze inside <thinking> tags.
    Image: [GENERATE_IMAGE: descriptive prompt]
    Language: Hinglish expert for Sanjeev.
    """
    
    # Try the most stable naming conventions first
    for m_name in ["gemini-1.5-flash", "models/gemini-1.5-flash", "gemini-pro"]:
        try:
            # Explicitly NOT using v1beta version strings here
            model = genai.GenerativeModel(model_name=m_name, system_instruction=instruction)
            return model
        except Exception:
            continue
    return None

def get_chat_response(model, user_input, history):
    if model is None: return "Agent error."
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
