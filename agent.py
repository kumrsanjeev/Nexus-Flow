import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Check Streamlit Secrets.")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    You are Nexus Flow AI. 
    1. IMAGE: If user asks for an image, respond ONLY with: [GENERATE_IMAGE: descriptive prompt]
    2. THINKING: For other queries, use <thinking> logic </thinking> then final answer.
    """
    
    try:
        # Step 1: Automatically find ANY available model in your account
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if not available_models:
            st.error("No models found for this API Key!")
            return None
            
        # Step 2: Pick the best one available (Priority: 1.5 Flash -> 1.5 Pro -> Pro -> Any)
        selected = None
        for target in ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]:
            if target in available_models:
                selected = target
                break
        
        if not selected:
            selected = available_models[0] # Fallback to whatever is available
            
        # Step 3: Initialize with the detected model name
        model = genai.GenerativeModel(model_name=selected, system_instruction=instruction)
        return model
        
    except Exception as e:
        # Final desperate fallback
        st.warning(f"Auto-detection failed, trying default gemini-pro...")
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
