import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing!")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Advanced System Instruction
    instruction = """
    You are Nexus Flow AI.
    1. IMAGE GENERATION: If user asks for an image, respond ONLY with: [GENERATE_IMAGE: prompt]
    2. REASONING: For others, use <thinking> step-by-step logic </thinking> then final answer.
    """
    
    # Direct model name without 'models/' often fixes the 404 on Streamlit Cloud
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash", 
        system_instruction=instruction
    )
    return model

def get_chat_response(model, user_input, history):
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
