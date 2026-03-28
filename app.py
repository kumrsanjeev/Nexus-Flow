import streamlit as st
import google.generativeai as genai
from openai import OpenAI

# --- Yahan apni Keys daalein ---
GEMINI_KEY = "YOUR_GEMINI_API_KEY_HERE"
OPENAI_KEY = "YOUR_OPENAI_API_KEY_HERE"

st.set_page_config(page_title="Nexus Flow Pro - Auto API", layout="wide")
st.title("🚀 Dual AI (Automatic Connection)")

user_query = st.chat_input("Sawal puchiye...")

if user_query:
    col1, col2 = st.columns(2)

    # Gemini Auto-Run
    with col1:
        st.subheader("✨ Gemini Response")
        try:
            genai.configure(api_key=GEMINI_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(user_query)
            st.info(res.text)
        except Exception as e:
            st.error(f"Gemini Error: {e}")

    # OpenAI Auto-Run
    with col2:
        st.subheader("🧠 OpenAI Response")
        try:
            client = OpenAI(api_key=OPENAI_KEY)
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": user_query}]
            )
            st.success(res.choices[0].message.content)
        except Exception as e:
            st.error(f"OpenAI Error: {e}")
