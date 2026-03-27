import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing!")
        return None
        
    # Using stable configuration
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    Role: Nexus Flow 'Universal' Pro.
    - Identity: Sanjeev's Digital Partner.
    - Thinking: Use <thinking> tags for reasoning.
    - Images: Respond ONLY with [GENERATE_IMAGE: descriptive prompt] for visuals.
    - Style: Professional Hinglish.
    """
    
    try:
        # Step 1: Force model discovery from the stable list
        available = [m.name for m in genai.list_models()]
        
        # Priority mapping to avoid 404
        selected = None
        for target in ["models/gemini-1.5-flash", "models/gemini-pro"]:
            if target in available:
                selected = target
                break
        
        if not selected:
            selected = "gemini-pro" # Hard fallback

        return genai.GenerativeModel(
            model_name=selected,
            system_instruction=instruction
        )
    except Exception as e:
        # Desperate fallback for 404/API issues
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    if model is None: return "Agent initialization failed."
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
