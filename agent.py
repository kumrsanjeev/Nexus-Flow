import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        return None
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # ChatGPT-style Deep Reasoning Instructions
    instruction = """
    You are Nexus Flow AI, a highly advanced reasoning model like ChatGPT/Gemini.
    
    CORE RULES:
    1. THINKING PROCESS: Before every answer, you must analyze the request inside <thinking> tags. 
       Break down the problem, verify facts, and plan a high-quality response.
    2. IMAGE GENERATION: If the user wants a photo/image, provide ONLY the tag: [GENERATE_IMAGE: descriptive prompt in English]
    3. TONE: Be helpful, witty, and use a mix of Hindi and English like a smart assistant for Sanjeev.
    4. KNOWLEDGE: You know about video editing (Punch Edit, Ghost Edit) and JEE/SAT preparation.
    """
    
    # Using 1.5 Flash for faster and smarter reasoning
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=instruction
    )
    return model

def get_chat_response(model, user_input, history):
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
