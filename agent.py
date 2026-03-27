import google.generativeai as genai
import streamlit as st

def initialize_agent():
    # Fetch API key from Streamlit secrets
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # System instruction to define your agent's personality
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction="You are Nexus Flow AI, a chatbot + automation agent. Be concise and helpful."
    )
    return model

def get_chat_response(model, user_input, history):
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
