import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing!")
        return None
        
    # Configure API
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Advanced System Instruction for Reasoning + Image detection
    instruction = """
    You are Nexus Flow AI. 
    1. IMAGE GENERATION: If user asks for an image, respond ONLY with: [GENERATE_IMAGE: prompt]
    2. REASONING: For others, use <thinking> step-by-step logic </thinking> then final answer.
    """
    
    # Try using the most stable model string for 2026
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash", # Remove 'models/' prefix
            system_instruction=instruction
        )
        return model
    except Exception:
        # Fallback to Pro if Flash is still causing 404
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
