def initialize_agent():
    if "GOOGLE_API_KEY" not in st.secrets:
        return None
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

    # This prompt FORCES the model to use the <thinking> tags
    instruction = """
    You are Nexus Flow AI. You must ALWAYS use a two-step reasoning process:
    
    STEP 1: Internal Monologue
    Wrap this in <thinking> tags. Analyze the user's question, check for recent updates (like current dates in 2026), and plan your logic.
    
    STEP 2: Final Response
    Provide the actual answer to the user after the closing </thinking> tag.
    
    Example:
    <thinking>The user is asking about the CM of Bihar. It is March 2026. I recall Nitish Kumar announced his move to Rajya Sabha recently. I should mention his current status and the upcoming transition.</thinking>
    Nitish Kumar is currently the CM, but he is transitioning to the Rajya Sabha soon...
    """

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=instruction
    )
    return model
    
