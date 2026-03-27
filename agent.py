import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing!")
        return None
    
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # --- DYNAMIC MODEL DETECTION ---
    try:
        # Aapke account mein available models ki list check karna
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Priority wise model select karna
        if 'models/gemini-1.5-flash' in models:
            selected_model = 'models/gemini-1.5-flash'
        elif 'models/gemini-pro' in models:
            selected_model = 'models/gemini-pro'
        else:
            selected_model = models[0] # Jo bhi pehla mile
            
    except Exception:
        selected_model = "gemini-pro" # Safe fallback

    "Example: [GENERATE_IMAGE: A high-tech dragon in 4k neon style]"
# AI ko bolo prompt plain text mein rakhe, koi symbols na use kare.
    
    
    return genai.GenerativeModel(model_name=selected_model, system_instruction=instruction)

def get_chat_response(model, user_input, history):
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
