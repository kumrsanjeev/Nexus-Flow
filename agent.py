import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    Role: Nexus Flow Pro. 
    1. Identity: Sanjeev's partner.
    2. Thinking: Use <thinking> tags for reasoning.
    3. Images: Use [GENERATE_IMAGE: descriptive prompt] for visuals.
    4. Language: Hinglish.
    """
    
    try:
        # Direct list scan to avoid 404
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        selected = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available else "models/gemini-pro"
        
        return genai.GenerativeModel(model_name=selected, system_instruction=instruction)
    except:
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    # This history format is critical for Memory
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
