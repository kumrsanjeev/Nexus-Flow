import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Advanced Thinking Prompt
    instruction = """
    You are Nexus Flow AI, a highly intelligent reasoning agent. 
    Before answering, you MUST think step-by-step.
    
    Format your response like this:
    <thinking>
    (In this section, analyze the user's intent, break down the facts, and plan your response. Do this internally.)
    </thinking>
    
    (Then, provide your final, polished, and helpful response here.)
    
    Always be concise, professional, and act as Sanjeev's personal automation partner.
    """
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=instruction
    )
    return model

def get_chat_response(model, user_input, history):
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
