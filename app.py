import streamlit as st
from agent import initialize_agent, get_chat_response
import re # for regex to detect image tags
import urllib.parse # for URL encoding of prompts

# Page configuration
st.set_page_config(page_title="Nexus Flow AI", page_icon="⚡", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .main { background-color: #0E1117; color: #FFFFFF; }
    .stChatInputContainer { border-top: 1px solid #262730; }
    .stChatMessage { border-radius: 12px; border: 1px solid #262730; padding: 10px; margin-bottom: 10px; }
    .stChatMessage.user { background-color: rgba(255, 255, 255, 0.05); }
    .stChatMessage.model { background-color: rgba(0, 150, 255, 0.05); }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #262730; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR & MENU ---
with st.sidebar:
    st.title("Nexus Flow 🤖")
    st.markdown("---")
    
    # 💾 Context History - Memory Management
    # This stores the history persistently for display
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # This stores history specifically formatted for the Gemini API
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [] # list of (prompt, response) tuples

    if st.button("🗑️ Clear Context (Memory)"):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.rerun()
    
    st.divider()
    st.caption("Developed by Sanjeev | JEE-SAT | CapCut Expert")

# Main Header
st.title("Nexus Flow AI ⚡")
st.write("Kaise help karu Sanjeev?")

# --- Display Messages Persistent History ---
# This loop handles re-displaying previous conversation turns (with images)
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if m["role"] == "user":
            st.markdown(f"👨 **Sanjeev:** {m['content']}")
        else:
            # Robot icon and response
            st.markdown(f"🤖 **Nexus:**")
            
            # Use regex to find image generation tag in the response
            # Format: [GENERATE_IMAGE: descriptive prompt]
            image_match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', m['content'])
            
            if image_match:
                # 🖼️ robust direct image display
                img_prompt = image_match.group(1).strip()
                # URL Encode spaces for safe link generation
                encoded_prompt = urllib.parse.quote(img_prompt)
                
                # reliable direct image generation link (pollinations AI)
                # This direct URL rendering bypasses previous blank block issues.
                img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux&nologo=true"
                
                st.image(img_url, caption=f"Nexus Flow Generated: {img_prompt}")
                # st.markdown(f"<img src='{img_url}' alt='{img_prompt}' style='max-width:100%; height:auto; border-radius:10px;'>", unsafe_allow_html=True)
                
                # Show cleaned text (removing the tag from display)
                cleaned_content = m['content'].replace(image_match.group(0), "").strip()
                if cleaned_content:
                    st.markdown(cleaned_content)
            else:
                st.markdown(m['content'])


# --- Main Conversation Input Logic ---
if prompt := st.chat_input("Puchiye Sanjeev..."):
    # 👨 **Display user prompt**
    with st.chat_message("user"):
        st.markdown(f"👨 **Sanjeev:** {prompt}")
        
    # Save user message to persistent history state
    st.session_state.messages.append({"role": "user", "content": prompt})

    # --- Nexus Bot Thinking ---
    with st.chat_message("model"):
        # Dropdown like thinking block
        with st.status("Thinking like Sanjeev...", expanded=False) as status:
            model = initialize_agent()
            
            # Send context history to the agent (Gemini history formatting logic is in agent.py)
            full_res = get_chat_response(model, prompt, st.session_state.chat_history)
            
            status.update(label="Reasoning Done!", state="complete")

        st.markdown(f"🤖 **Nexus:**")
        
        # Regex to check for image generation in this turn
        image_match = re.search(r'\[GENERATE_IMAGE:\s*(.*?)\]', full_res)
        
        if image_match:
            # Direct Image Display turn logic
            img_prompt = image_match.group(1).strip()
            encoded_prompt = urllib.parse.quote(img_prompt)
            img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux&nologo=true"
            
            st.image(img_url, caption=f"Nexus Flow Generated: {img_prompt}")
            
            cleaned_full_res = full_res.replace(image_match.group(0), "").strip()
            if cleaned_full_res:
                st.markdown(cleaned_full_res)
        else:
            # Normal text response
            st.markdown(full_res)

    # --- Save full context turn (memory) ---
    # User part of context
    # API context (strictly user/model parts format)
    st.session_state.chat_history.append((prompt, full_res))
    
    # Message persistent history part
    st.session_state.messages.append({"role": "model", "content": full_res})
    
