# Agent.py
# Predefined Q&A dictionary
qa_dict = {
    "pm of india": "Narendra Modi is the Prime Minister of India.",
    "cm of india": "India has no single CM; each state has its own CM."
}

def get_answer(question):
    """
    Returns the answer if question exists in dictionary, else an error message.
    """
    key = question.strip().lower()  # Fix: lowercase & remove extra spaces
    if key in qa_dict:
        return qa_dict[key]
    else:
        return "❌ Error! Question not recognized."
