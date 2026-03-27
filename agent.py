import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Check Streamlit Secrets.")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    You are Nexus Flow AI, Sanjeev's digital partner.
    1. REASONING: Analyze every query deeply inside <thinking> tags.
    2. IMAGES: Respond ONLY with [GENERATE_IMAGE: prompt] for visual requests.
    3. MEMORY: Remember previous context from chat history.
    """
    
    try:
        # Step 1: Get all available models for your API key
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Step 2: Priority selection to avoid 404
        selected = None
        for target in ["models/gemini-1.5-flash", "models/gemini-pro", "models/gemini-1.5-pro"]:
            if target in available_models:
                selected = target
                break
        
        # Fallback to the first available if none of the above match
        if not selected and available_models:
            selected = available_models[0]
            
        if not selected:
            st.error("No compatible models found for this API Key.")
            return None

        return genai.GenerativeModel(model_name=selected, system_instruction=instruction)
    except Exception as e:
        st.error(f"Initialization Error: {e}")
        return None

def get_chat_response(model, user_input, history):
    # History format: [{'role': 'user', 'parts': [...]}, {'role': 'model', 'parts': [...]}]
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
