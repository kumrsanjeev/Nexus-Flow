import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Check Secrets.")
        return None
        
    # FIX: Using stable configuration (No v1beta)
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    Role: Nexus Flow Pro. 
    1. Identity: Sanjeev's partner. Expert in Video Editing & JEE.
    2. Thinking: Deep reasoning inside <thinking> tags.
    3. Image: ONLY use [GENERATE_IMAGE: descriptive prompt] for visuals.
    """
    
    try:
        # Step 1: Force find stable models
        available = [m.name for m in genai.list_models()]
        selected = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available else "models/gemini-pro"
        
        return genai.GenerativeModel(model_name=selected, system_instruction=instruction)
    except Exception:
        # Emergency fallback
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    if model is None: return "Agent Error."
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
