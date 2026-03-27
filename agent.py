import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing!")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # --- AUTO-DETECTION LOGIC ---
    # We will try to find the best available model automatically
    try:
        available_models = [m.name for m in genai.list_models() 
                            if 'generateContent' in m.supported_generation_methods]
        
        # Priority list: we want Flash 1.5, but will take anything that works
        target_models = ["models/gemini-1.5-flash", "models/gemini-pro", "models/gemini-1.0-pro"]
        
        selected_model = None
        for target in target_models:
            if target in available_models:
                selected_model = target
                break
        
        # If none of our targets match exactly, take the first one available
        if not selected_model and available_models:
            selected_model = available_models[0]
            
        if selected_model:
            return genai.GenerativeModel(model_name=selected_model)
        else:
            st.error("No compatible Gemini models found for this API Key.")
            return None
            
    except Exception as e:
        st.error(f"Failed to list models: {e}")
        # Fallback to a safe default
        return genai.GenerativeModel(model_name="gemini-1.5-flash")

def get_chat_response(model, user_input, history):
    if model is None:
        return "System Error: Model not initialized."
    
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
