import streamlit as st
import google.generativeai as genai

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="Nexus Flow Pro")

# ----------------- SESSION STATE -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory" not in st.session_state:
    st.session_state.memory = []

# ----------------- MODEL INITIALIZATION -----------------
def initialize_agent():
    # Check API key
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Google API key st.secrets me nahi hai!")
        return None
    
    # Configure API
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # List available models
    try:
        available_models = [m.name for m in genai.list_models()]
    except Exception as e:
        st.error(f"Error listing models: {
