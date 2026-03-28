import streamlit as st
import google.generativeai as genai
from openai import OpenAI

st.set_page_config(page_title="Nexus Flow Pro - Dual AI", layout="wide")
st.title("🤖 Gemini vs OpenAI Comparison")

# Sidebar for Setup
with st.sidebar:
    st.header("API Configuration")
    gemini_key = st.text_input("Gemini API Key:", type="password")
    openai_key = st.text_input("OpenAI API Key:", type="password")
    st.info("Dono keys enter karein comparison ke liye.")

# Input Field
user_query = st.text_input("Aapka Sawal:", placeholder="e.g., Prime Minister of India kaun hai?")

if st.button("Generate Response") and user_query:
    if not gemini_key or not openai_key:
        st.warning("Kripya dono API keys sidebar mein enter karein.")
    else:
        # Create two columns for side-by-side comparison
        col1, col2 = st.columns(2)

        # --- Gemini Section ---
        with col1:
            st.subheader("✨ Google Gemini")
            try:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                gemini_res = model.generate_content(user_query)
                st.info(gemini_res.text)
            except Exception as e:
                st.error(f"Gemini Error: {e}")

        # --- OpenAI Section ---
        with col2:
            st.subheader("🧠 OpenAI GPT-4o")
            try:
                client = OpenAI(api_key=openai_key)
                openai_res = client.chat.completions.create(
                    model="gpt-4o-mini", # Ya "gpt-4" use karein
                    messages=[{"role": "user", "content": user_query}]
                )
                st.success(openai_res.choices[0].message.content)
            except Exception as e:
                st.error(f"OpenAI Error: {e}")

# Footer
st.divider()
st.caption("Powered by Nexus Flow Pro Engine")
