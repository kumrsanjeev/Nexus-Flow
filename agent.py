import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing!")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    You are Nexus Flow AI, Sanjeev's partner. 
    1. Think deeply inside <thinking> tags.
    2. For images, use ONLY: [GENERATE_IMAGE: descriptive prompt]
    3. Use Hinglish naturally.
    """
    
    try:
        # Step 1: Scan for all available models
        # Ye line 404 error ko hamesha ke liye khatam kar degi
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Step 2: Pick the best one available in YOUR account
        selected = None
        for target in ["models/gemini-1.5-flash", "models/gemini-pro", "models/gemini-1.5-pro"]:
            if target in available_models:
                selected = target
                break
        
        if not selected and available_models:
            selected = available_models[0]
            
        if not selected:
            return None

        return genai.GenerativeModel(model_name=selected, system_instruction=instruction)
    except Exception as e:
        # Final desperate fallback to standard name
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    if model is None: return "Error: Model initialization failed."
    # Direct chat session with history
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
