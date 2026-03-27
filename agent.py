import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Add it to Secrets.")
        return None
        
    # FIX: No version string, purely stable config
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # System Instruction for Advanced Logic
    instruction = """
    You are Nexus Flow AI Pro. 
    1. REASONING: Always think deeply inside <thinking> tags.
    2. IMAGE: For visuals, use [GENERATE_IMAGE: English prompt].
    3. PERSONALITY: You are Sanjeev's digital partner.
    """
    
    try:
        # Step 1: Force find stable models only
        available_models = [m.name for m in genai.list_models()]
        
        # Priority selection to avoid 404
        selected = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available_models else "models/gemini-pro"
        
        return genai.GenerativeModel(model_name=selected, system_instruction=instruction)
    except Exception:
        # Final emergency fallback
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    if model is None: return "Agent Error."
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
