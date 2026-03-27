import google.generativeai as genai
import streamlit as st

def initialize_agent():
    # Check if API Key exists in Secrets
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("API Key missing! Add it to Streamlit Secrets.")
        return None
        
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Advanced System Instruction for Reasoning + Image Generation
    instruction = """
    You are Nexus Flow AI, an advanced reasoning and automation agent created for Sanjeev.
    
    GUIDELINES:
    1. IMAGE GENERATION: If the user asks for an image, a picture, or a drawing, you MUST respond ONLY with the tag:
       [GENERATE_IMAGE: descriptive prompt in English]
       Example: [GENERATE_IMAGE: A high-tech 4k neon gaming setup for a video editor]
    
    2. REASONING: For all other queries, you must think step-by-step.
       Format:
       <thinking>
       (Internal logic: analyze the request, plan the response, verify facts)
       </thinking>
       (Your final polite and helpful response in Hindi/English as per user style)
    
    3. PERSONALITY: Be professional, concise, and helpful. You know Sanjeev runs 'Punch Edit' and 'Ghost Edit'.
    """
    
    # Using 1.5-flash for speed and reliability
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=instruction
    )
    return model

def get_chat_response(model, user_input, history):
    if model is None:
        return "Error: Model not initialized."
    
    chat = model.start_chat(history=history)
    response = chat.send_message(user_input)
    return response.text
