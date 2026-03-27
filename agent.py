import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing!")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Advanced Thinking + Image Instruction
    instruction = """
    You are Nexus Flow AI, a deep reasoning model.
    1. REASONING: Analyze every request inside <thinking> tags step-by-step.
    2. IMAGES: If user wants an image, respond ONLY with: [GENERATE_IMAGE: descriptive prompt in English]
    3. PERSONALITY: Be smart, use Hindi-English mix, and support Sanjeev's editing and studies.
    """
    
    # Try different naming conventions to bypass the 404 error
    for model_name in ["models/gemini-1.5-flash", "gemini-1.5-flash", "models/gemini-pro"]:
        try:
            model = genai.GenerativeModel(model_name=model_name, system_instruction=instruction)
            return model
        except:
            continue
    return None

def get_chat_response(model, user_input, history):
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
