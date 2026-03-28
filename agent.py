import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Add it to Streamlit Secrets.")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # System Instruction for Thinking + Images
    instruction = """
    You are Nexus Flow AI. 
    1. IMAGE: For image requests, respond ONLY with: [GENERATE_IMAGE: descriptive prompt in English]
    2. THINKING: For others, use <thinking> step-by-step logic </thinking> then final answer.
    """
    
    try:
        # Automatically find the best working model for your API key
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        selected = "models/gemini-1.5-flash" # Default target
        if selected not in available_models:
            selected = "models/gemini-pro"
        if selected not in available_models and available_models:
            selected = available_models[0]

        return genai.GenerativeModel(model_name=selected, system_instruction=instruction)
    except:
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
