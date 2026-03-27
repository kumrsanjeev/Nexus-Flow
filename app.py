# App.py
import streamlit as st
from Agent import get_answer

st.set_page_config(page_title="Simple Chatbot", page_icon="🤖")
st.title("🤖 Simple Chatbot")

# User input
user_question = st.text_input("Ask a question:")

if user_question:
    answer = get_answer(user_question)
    if "Error" in answer:
        st.error(answer)
    else:
        st.success(answer)
