import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Add it to Streamlit Secrets.")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Advanced System Instruction
    instruction = """
    You are Nexus Flow AI. 
    1. IMAGE: If user asks for an image, respond ONLY with: [GENERATE_IMAGE: descriptive prompt]
    2. THINKING: For other queries, use <thinking> step-by-step logic </thinking> then final answer.
    """
    
    # Using 'gemini-pro' as it is the most compatible fallback for 404 errors
    model = genai.GenerativeModel(
        model_name="gemini-pro", 
        system_instruction=instruction
    )
    return model

def get_chat_response(model, user_input, history):
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
