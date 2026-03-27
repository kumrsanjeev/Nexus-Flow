import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing in Secrets!")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    Role: Nexus Flow Pro. 
    Memory: You remember everything from the history.
    Thinking: Use <thinking> logic </thinking> for every answer.
    Image: Use [GENERATE_IMAGE: descriptive prompt] for visuals.
    Language: Expert in Hinglish, C++, and Video Editing.
    """
    
    try:
        # Step 1: Scan for ALL active models in your account
        # Ye loop har account ke liye kaam karega
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        selected = None
        # Priority mapping
        for target in ["models/gemini-1.5-flash", "models/gemini-pro", "gemini-pro"]:
            if target in available_models:
                selected = target
                break
        
        if not selected and available_models:
            selected = available_models[0]
            
        if not selected: return None

        return genai.GenerativeModel(model_name=selected, system_instruction=instruction)
    except Exception as e:
        # Final fallback to standard pro
        try: return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)
        except: return None

def get_chat_response(model, user_input, history):
    if model is None: return "Agent not initialized. Check API Key."
    try:
        chat = model.start_chat(history=history)
        response = chat.send_message(user_input)
        return response.text
    except Exception as e:
        if "429" in str(e): return "⚠️ Quota full! Please wait 60 seconds."
        return f"API Error: {str(e)}"
        
