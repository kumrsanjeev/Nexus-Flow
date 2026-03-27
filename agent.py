import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Check Streamlit Secrets.")
        return None
        
    # FIX 1: Configure with the stable endpoint only
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    instruction = """
    You are Nexus Flow AI. 
    1. REASONING: Think deeply inside <thinking> tags.
    2. IMAGE: Use [GENERATE_IMAGE: prompt] for visual requests.
    3. IDENTITY: You are Sanjeev's digital avatar. Expert in CapCut, C++, and SAT.
    """
    
    try:
        # FIX 2: Dynamic Model Detection to bypass 404
        # Ye aapke account ke saare zinda models ki list nikalega
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Priority mapping to select the best available one
        selected = None
        for target in ["models/gemini-1.5-flash", "models/gemini-pro", "gemini-pro"]:
            if target in available_models:
                selected = target
                break
        
        if not selected and available_models:
            selected = available_models[0]
            
        if not selected:
            st.error("No models found for this API Key. Check Billing/Quota on Google AI Studio.")
            return None

        # FIX 3: Initialize without forcing any version string
        return genai.GenerativeModel(model_name=selected, system_instruction=instruction)
        
    except Exception as e:
        # Final emergency fallback if list_models fails
        try:
            return genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=instruction)
        except:
            st.error(f"Critical System Error: {e}")
            return None

def get_chat_response(model, user_input, history):
    if model is None: return "Agent not ready."
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
    
