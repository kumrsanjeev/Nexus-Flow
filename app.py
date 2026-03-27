import streamlit as st
# CRITICAL: Page config must be the very first line
st.set_page_config(page_title="Nexus Flow | Context Pro", page_icon="⚡", layout="wide")

from agent import initialize_agent, get_chat_response
import urllib.parse
import re

# Custom CSS for UI
st.markdown("<style>.stChatMessage { border-radius: 12px; border: 1px solid #30363d; }</style>", unsafe_allow_html=True)

# Session State for Messages & API Formatting
if "messages" not in st.session_state:
    st.session_state.messages = [] # For display
if "api_history" not in st.session_state:
    st.session_state.api_history = [] # For API context (roles: 'user', 'model')

# Sidebar for controls
with st.sidebar:
    st.title("Nexus Flow Pro 🤖")
    st.write("Mode: Universal Intelligence")
    st.info("Status: Online 🟢")
    if st.button("🗑️ Clear Memory"):
        st.session_state.messages = []
        st.session_state.api_history = [] # Must clear API history too
        st.rerun()
    st.divider()
    st.caption("Developed by Sanjeev | Context v1.0")

# 1. Image Parser for Direct Gemini Display
def parse_and_display_response(raw_text):
    # Regex to find the [GENERATE_IMAGE: prompt] tag
    image_match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', raw_text)
    
    if image_match:
        # Step A: Clean response from image tag
        clean_ans = raw_text.replace(image_match.group(0), "").strip()
        img_prompt = image_match.group(1).strip()
        encoded_p = urllib.parse.quote(img_prompt)
        # Flux high-quality image URL
        img_url = f"https://image.pollinations.ai/prompt/{encoded_p}?width=1024&height=1024&model=flux&nologo=true"
        
        return clean_ans, img_url, img_prompt
    else:
        return raw_text, None, None

# 2. Display Message History
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image_url" in m and m["image_url"]:
            st.image(m["image_url"], caption=f"Generated for Sanjeev: {m['image_caption']}")

# 3. Main Input Logic
if prompt := st.chat_input("Puchiye Sanjeev..."):
    # Add to display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Nexus Flow is thinking deeply...", expanded=False) as status:
            try:
                # Use context-robust initialization
                model = initialize_agent()
                
                # Step B: Get response using strictly formatted api_history
                # Context is passed HERE. It's the memory of the conversation.
                full_res = get_chat_response(model, prompt, st.session_state.api_history)
                
                final_output = ""
                img_url = None
                img_caption = None
                
                # Step C: Parse Thinking Logic first
                thinking_match = re.search(r'<thinking>(.*?)</thinking>', full_res, re.DOTALL)
                if thinking_match:
                    thinking_txt = thinking_match.group(1).strip()
                    st.info(f"🧠 Reasoning: {thinking_txt}") # Reasoning inside status
                    full_res = full_res.replace(thinking_match.group(0), "").strip()
                
                # Step D: Parse Image and Final Answer
                final_output, img_url, img_caption = parse_and_display_response(full_res)
                
                if final_output:
                    status.update(label="Reasoning complete!", state="complete")
                
                # Step E: Formatting data for saving in context
                # Crucial for Memory: We save the *final output* to history.
                st.session_state.api_history.append({"role": "user", "parts": [prompt]})
                st.session_state.api_history.append({"role": "model", "parts": [final_output]})
                
            except Exception as e:
                final_output = f"System Error: {e}"
                status.update(label="Failed!", state="error")

        # Display Final Response
        st.markdown(final_output)
        
        # Display Image if generated
        if img_url:
            st.image(img_url, caption=f"Created: {img_caption}")
        
        # Save to messages history with optional image data
        msg_data = {"role": "assistant", "content": final_output}
        if img_url:
            msg_data["image_url"] = img_url
            msg_data["image_caption"] = img_caption
        st.session_state.messages.append(msg_data)
        
