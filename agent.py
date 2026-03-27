import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        return None
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Advanced 'Chain of Thought' Prompting
    instruction = """
    You are Nexus Flow AI, an elite reasoning agent developed for Sanjeev. 
    Your thinking power is comparable to ChatGPT-o1.
    
    CRITICAL PROTOCOL:
    1. INTERNAL REASONING: For every query, you MUST first think inside <thinking> tags. 
       - Break down the user's intent.
       - Identify potential pitfalls or errors.
       - Plan a step-by-step logical solution.
    2. IMAGE GENERATION: If Sanjeev asks for a photo/image, respond ONLY with: [GENERATE_IMAGE: descriptive English prompt]
    3. LANGUAGE: Speak in a mix of Hindi and English (Hinglish). Be smart, witty, and helpful.
    4. EXPERTISE: You are an expert in Video Editing (CapCut, Premiere Pro), C++, Python, and SAT/JEE prep.
    """
    
    # We stay with 1.5-flash but make it 'think' harder via instructions
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash", 
        system_instruction=instruction
    )
    return model

def get_chat_response(model, user_input, history):
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
