import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Check Streamlit Secrets.")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Advanced System Instruction
    instruction = """
    You are 'Nexus Flow AI', Sanjeev's personal digital avatar.
    1. THINKING: You MUST analyze every request inside <thinking> tags.
    2. IMAGES: For image requests, respond ONLY with: [GENERATE_IMAGE: descriptive prompt]
    3. STYLE: Use a mix of Hindi and English. Be professional and helpful for JEE/SAT and Video Editing.
    """
    
    try:
        # Step 1: Scan for working models to avoid 404
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Priority list
        selected = None
        for target in ["models/gemini-1.5-flash", "models/gemini-pro", "models/gemini-1.5-pro"]:
            if target in available_models:
                selected = target
                break
        
        if not selected and available_models:
            selected = available_models[0]
            
        return genai.GenerativeModel(model_name=selected, system_instruction=instruction)
    except Exception:
        # Safe fallback
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    if model is None: return "Agent error: Initialization failed."
    
    try:
        chat = model.start_chat(history=history)
        response = chat.send_message(user_input)
        
        # SAFETY CHECK: If response is empty or blocked
        if response.candidates and len(response.candidates[0].content.parts) > 0:
            return response.text
        else:
            return "⚠️ Maaf kijiye Sanjeev, ye topic safety filters ki wajah se block ho gaya hai. Please try another question."
            
    except Exception as e:
        return f"Error: {str(e)}"
        
