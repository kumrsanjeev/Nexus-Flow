import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Check Streamlit Secrets.")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Advanced System Instruction for Reasoning + Images
    instruction = """
    You are Nexus Flow AI. 
    1. IMAGE GENERATION: If user asks for an image, respond ONLY with: [GENERATE_IMAGE: descriptive prompt]
    2. REASONING: For other queries, use <thinking> step-by-step logic </thinking> then final answer.
    Be professional and act as Sanjeev's partner.
    """
    
    # Direct model names - Most stable for 2026 SDK
    try:
        # Try Flash first (Fastest)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=instruction
        )
        return model
    except Exception:
        # Fallback to Pro if Flash fails
        try:
            return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)
        except Exception as e:
            st.error(f"Critical Error: {e}")
            return None

def get_chat_response(model, user_input, history):
    if model is None: return "Agent not initialized."
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
