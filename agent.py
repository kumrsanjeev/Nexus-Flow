import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing!")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    You are Nexus Flow AI, Sanjeev's personal intelligence partner.
    - REASONING: Analyze every query deeply.
    - IMAGES: Respond ONLY with [GENERATE_IMAGE: prompt] for visual requests.
    - IDENTITY: You were created by Sanjeev. You are expert in Video Editing & JEE/SAT.
    """
    
    try:
        # Automatic model selection to avoid 404
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        selected = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available else "models/gemini-pro"
        
        return genai.GenerativeModel(model_name=selected, system_instruction=instruction)
    except:
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    # GEMINI FORMAT: [{'role': 'user', 'parts': [...]}, {'role': 'model', 'parts': [...]}]
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
