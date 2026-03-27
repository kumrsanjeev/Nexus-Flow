import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing!")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    Role: Nexus Flow 'Universal' Pro.
    - Identity: Sanjeev's Digital Partner.
    - Memory: You have 100% context retention. Remember everything from chat history.
    - Thinking: Use <thinking> tags for deep reasoning.
    - Images: Respond ONLY with [GENERATE_IMAGE: descriptive prompt] for visuals.
    - Style: Professional Hinglish. Expert in Video Editing, Coding, and SAT/JEE.
    """
    
    # --- PRO FIX: Model Discovery ---
    try:
        # Check if 1.5-flash is available first
        model_name = "models/gemini-1.5-flash"
        try:
            genai.get_model(model_name)
        except:
            model_name = "models/gemini-pro"
            
        return genai.GenerativeModel(
            model_name=model_name,
            system_instruction=instruction
        )
    except Exception as e:
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    if model is None: return "Agent initialization failed."
    # Gemini strictly needs 'user' and 'model' roles
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
