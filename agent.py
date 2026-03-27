from openai import OpenAI
import streamlit as st

def initialize_agent():
    if "OPENAI_API_KEY" not in st.secrets:
        st.error("OpenAI API Key missing! Add it to Streamlit Secrets.")
        return None
    
    # Initialize OpenAI Client
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    return client

def get_chat_response(client, user_input, history):
    # System Instruction for ChatGPT-like Brain
    messages = [
        {"role": "system", "content": """
            You are Nexus Flow AI Pro. 
            - PERSONALITY: Expert, logical, and witty like GPT-4o.
            - REASONING: For complex tasks, think step-by-step inside <thinking> tags.
            - IMAGES: For image requests, respond ONLY with: [GENERATE_IMAGE: detailed English prompt]
            - CONTEXT: You are Sanjeev's partner in Video Editing and Coding.
        """}
    ]
    
    # Add history to context
    for msg in history:
        messages.append(msg)
    
    # Add current user input
    messages.append({"role": "user", "content": user_input})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Aap gpt-3.5-turbo bhi use kar sakte hain
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI Error: {e}"
        
