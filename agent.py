import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Check Streamlit Secrets.")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Personal Identity for the Model
    instruction = """
    You are 'Sanjeev ka Digital Avatar' (Nexus Flow AI). 
    You are a high-level reasoning agent specialized in Video Editing (Ghost/Punch Edit), 
    Coding (Python, C++), and SAT/JEE Preparation.
    
    PROTOCOLS:
    1. THINKING: Always analyze requests step-by-step inside <thinking> tags.
    2. IMAGES: For image requests, respond ONLY with: [GENERATE_IMAGE: descriptive prompt]
    3. STYLE: Use a mix of Hindi and English. Be smart and professional.
    """
    
    try:
        # Step 1: Scan for all available models to avoid 404
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Step 2: Pick the best one (Priority: 1.5 Flash -> 1.5 Pro -> Pro -> Any)
        selected_model = None
        for target in ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]:
            if target in available_models:
                selected_model = target
                break
        
        if not selected_model and available_models:
            selected_model = available_models[0]
            
        if selected_model:
            return genai.GenerativeModel(model_name=selected_model, system_instruction=instruction)
        else:
            return None
            
    except Exception as e:
        # Fallback to the most basic stable name
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    if model is None: return "Agent error: Check API permissions."
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
