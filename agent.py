import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Check Secrets.")
        return None
        
    # FIX: No version string, let the library pick the stable one
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    try:
        # Step 1: Get list of all available models for your key
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Step 2: Priority selection (Flash is faster and cheaper)
        selected = None
        for target in ["models/gemini-1.5-flash", "models/gemini-pro"]:
            if target in available_models:
                selected = target
                break
        
        if not selected and available_models:
            selected = available_models[0]
            
        # FIX: No version prefix here either
        model = genai.GenerativeModel(model_name=selected)
        return model
    except Exception as e:
        # Final fallback if everything fails
        return genai.GenerativeModel(model_name="gemini-pro")

def get_chat_response(model, user_input, history):
    if model is None: return "Agent Error."
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
