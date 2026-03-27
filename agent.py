import google.generativeai as genai
import streamlit as st

def initialize_agent():
    # Retrieve API key from Streamlit secrets
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("GOOGLE_API_KEY is missing from Streamlit secrets.")
        return None
        
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # --- Advanced System Instruction for Image Generation & Context ---
    instruction = """
    You are 'Nexus Flow AI', developed by Sanjeev. You are a professional assistant specialized in:
    1. Video Editing (Ghost Edit, Punch Edit, CapCut, Premiere Pro)
    2. Coding (C++, Python)
    3. Exam Preparation (JEE, SAT)

    KEY CAPABILITIES & RULES:
    1. IDENTITY: Always introduce yourself as Nexus Flow AI when asked about identity. Say Sanjeev is your owner.
    2. IMAGE GENERATION: When the user asks to generate an image or see something (e.g., 'Dragon dikhao', 'Generate an image of a car'), you MUST respond using this exact format ONLY, at the start of your message: [GENERATE_IMAGE: highly descriptive image prompt in English] followed by any relevant Hinglish response. Do not generate code or text answers for image requests. Keep the prompt descriptive for better results.
    3. LANGUAGE: Prefer Hinglish (Hindi + English) like a local Indian assistant. Be polite and professional.
    4. CONTEXT: Remember that Sanjeev is a student and editor. Tailor your examples to these fields.
    """
    
    # Fallback to gemini-pro if flash 1.5 is unavailable (fixes some region issues)
    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=instruction)
        return model
    except Exception:
        # If gemini-1.5-flash is not available for this key/region
        st.warning("gemini-1.5-flash not available. Falling back to gemini-pro.")
        model = genai.GenerativeModel(model_name="gemini-pro", system_instruction=instruction)
        return model

def get_chat_response(model, user_input, history):
    if model is None:
        return "System Error: Model not initialized. Check API Key."
        
    try:
        # strictly Gemini requires history in 'user' and 'model' parts format
        # This formatting fix resolves the chat history issue.
        formatted_history = []
        for turn in history:
            # turn should be a tuple (prompt, response) from st.session_state.chat_history
            if len(turn) == 2:
                formatted_history.append({"role": "user", "parts": [turn[0]]})
                formatted_history.append({"role": "model", "parts": [turn[1]]})

        # Start a persistent chat instance with formatted history
        chat = model.start_chat(history=formatted_history)
        
        # Send the message and get response
        response = chat.send_message(user_input)
        
        # Safe response accessing (prevents blank part error)
        if response.candidates and len(response.candidates[0].content.parts) > 0:
            return response.text
        else:
            return "Maaf kijiye, main ye topic safety policies ke wajah se respond nahi kar sakta. Kuch aur puchiye?"
            
    except Exception as e:
        return f"Oops, error aa gaya: {str(e)}"
        
