import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Check Streamlit Secrets.")
        return None
        
    # FIX: No version string, uses the latest stable v1 automatically
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    You are Nexus Flow AI Pro. 
    1. REASONING: Always think deeply and logically like ChatGPT inside <thinking> tags.
    2. IMAGES: For image requests, respond ONLY with: [GENERATE_IMAGE: descriptive prompt]
    3. PERSONALITY: You are Sanjeev's expert partner in Video Editing, Coding, and SAT.
    """
    
    try:
        # Priority: Flash for speed, Pro for backup
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=instruction)
        return model
    except:
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    if not model: return "Agent Error."
    # FIX: history naming to avoid TypeError
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
