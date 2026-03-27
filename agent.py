import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Secrets mein API Key nahi mili!")
        return None
    
    # FIX: Sirf API Key configure karein, koi version string nahi
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Direct model name use karein bina kisi prefix ya v1beta ke
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model
    except Exception:
        return genai.GenerativeModel("gemini-pro")

def get_chat_response(model, user_input, history):
    if not model: return "Model initialize nahi hua."
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
