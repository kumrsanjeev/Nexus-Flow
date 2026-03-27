import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing!")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Try different naming conventions to bypass the 404 error
    # We prioritize 1.5-flash but provide fallbacks
    for model_name in ["gemini-1.5-flash", "models/gemini-1.5-flash", "gemini-pro"]:
        try:
            model = genai.GenerativeModel(model_name=model_name)
            return model
        except:
            continue
    return None

def get_chat_response(model, user_input, history):
    if model is None: return "Agent could not be initialized."
    try:
        chat = model.start_chat(history=history)
        response = chat.send_message(user_input)
        return response.text
    except Exception as e:
        if "429" in str(e):
            return "⚠️ Quota Full! Please wait 60 seconds."
        return f"API Error: {str(e)}"
