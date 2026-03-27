import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Check Secrets.")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    Role: Nexus Flow Pro. 
    1. Always use <thinking> logic </thinking> first.
    2. Image Tag: [GENERATE_IMAGE: descriptive prompt]
    3. Language: Hinglish expert.
    """
    
    # Try all possible names in a simple loop
    for m_name in ["gemini-1.5-flash", "models/gemini-1.5-flash", "gemini-pro"]:
        try:
            model = genai.GenerativeModel(model_name=m_name, system_instruction=instruction)
            return model
        except:
            continue
    return None

def get_chat_response(model, user_input, history):
    if model is None: return "Agent error."
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
