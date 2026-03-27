import google.generativeai as genai
import streamlit as st

def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Check Streamlit Secrets.")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # 🌍 UNIVERSAL INTELLIGENCE & REASONING INSTRUCTION
    instruction = """
    Role: Nexus Flow 'Universal' Pro (Sanjeev's Digital Avatar).
    Identity: You are a high-level reasoning agent with 100% accuracy in understanding ANY language (English, Hindi, Hinglish, Bhojpuri, etc.).
    
    CORE CAPABILITIES:
    1. SEMANTIC UNDERSTANDING: Understand the 'intent' and 'emotion' behind words, not just literal meaning.
    2. DEEP REASONING: Always analyze complex queries inside <thinking> tags before giving the final answer.
    3. SPECIALIZATION: Expert in Video Editing (Ghost/Punch Edit style), Coding (C++, Python), and SAT/JEE Prep.
    4. IMAGE GEN: If Sanjeev wants an image, respond ONLY with: [GENERATE_IMAGE: descriptive prompt in English]
    5. PERSONALITY: Be witty, professional, and act as a smart partner to Sanjeev.
    """
    
    # Advanced Configuration for Language Power
    generation_config = {
        "temperature": 0.8, 
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }

    try:
        # Step 1: Scan for working models to avoid 404
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Priority Check
        selected = None
        for target in ["models/gemini-1.5-flash", "models/gemini-pro", "models/gemini-1.5-pro"]:
            if target in available_models:
                selected = target
                break
        
        if not selected and available_models:
            selected = available_models[0]
            
        return genai.GenerativeModel(
            model_name=selected, 
            system_instruction=instruction,
            generation_config=generation_config
        )
    except Exception:
        return genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)

def get_chat_response(model, user_input, history):
    if model is None: return "Agent initialization failed."
    try:
        chat = model.start_chat(history=history)
        response = chat.send_message(user_input)
        
        # Safety Check to prevent crashes
        if response.candidates and len(response.candidates[0].content.parts) > 0:
            return response.text
        return "⚠️ I couldn't process that language/content due to safety filters. Try again."
    except Exception as e:
        return f"System Error: {str(e)}"

