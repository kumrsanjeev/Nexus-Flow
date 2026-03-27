import google.generativeai as genai
import streamlit as st

def initialize_agent():
    # API Key check
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Add it to Streamlit Secrets.")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Dynamic Model Selection to avoid 404
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if 'models/gemini-1.5-flash' in available_models:
            model_id = 'models/gemini-1.5-flash'
        else:
            model_id = 'models/gemini-pro'
    except:
        model_id = 'gemini-1.5-flash'

    # Advanced System Instruction
    instruction = """
    You are Nexus Flow AI, an advanced reasoning agent for Sanjeev.
    
    1. IMAGE GENERATION: If user asks for an image/picture, respond ONLY with: 
       [GENERATE_IMAGE: descriptive prompt in English]
    
    2. REASONING: For other queries, you MUST think step-by-step.
       Format:
       <thinking>
       (Internal logic and planning)
       </thinking>
       (Your final helpful response)
    
    Be concise and professional.
    """
    
    return genai.GenerativeModel(model_name=model_id, system_instruction=instruction)

def get_chat_response(model, user_input, history):
    if model is None: return "Model not initialized."
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
