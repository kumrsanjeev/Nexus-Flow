import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Add it to Streamlit Secrets.")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # ChatGPT-style Advanced Instruction
    instruction = """
    You are Nexus Flow AI Pro, a highly intelligent assistant for Sanjeev.
    - PERSONALITY: Expert, witty, and extremely logical like GPT-4.
    - REASONING: For every complex question, ALWAYS think step-by-step inside <thinking> tags.
    - IMAGES: If Sanjeev asks to draw/generate/show an image, respond ONLY with: [GENERATE_IMAGE: highly detailed English prompt]
    - KNOWLEDGE: You know about Sanjeev's interest in Video Editing (Punch Edit), SAT/JEE, and Anime.
    - HINGLISH: Use a natural mix of Hindi and English.
    """
    
    try:
        # Forcing Gemini 1.5 Flash for better reasoning + speed
        return genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=instruction)
    except:
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    if not model: return "Model error."
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
