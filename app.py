import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv() # Loads variables from .env

# Set a title for the Streamlit app
st.title("Chatbot")

# Set the API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create a Gemini model instance with a known valid model name.
# The previous model name was causing an "InvalidArgument" error.
model = genai.GenerativeModel(os.getenv("GEMINI_MODEL"))

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to get the chat history in the correct format for the Gemini API
def get_api_history():
    history = []
    for msg in st.session_state.messages:
        # The Gemini API expects a list of dictionaries, each with a 'role' and 'parts' key.
        # The 'parts' key's value should be a list of dictionaries with a 'text' key.
        if "role" in msg and "content" in msg:
            # Map the Streamlit role 'assistant' to the Gemini API role 'model'
            api_role = 'model' if msg['role'] == 'assistant' else msg['role']
            history.append({"role": api_role, "parts": [{"text": msg["content"]}]})
    return history

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Convert history to the API's aexpected format
    api_history = get_api_history()
    
    # Create a chat session with the correctly formatted history
    # The last message is the current user's prompt, so we don't need to add it to the history
    chat_history_for_api = api_history[:-1]
    
    # Start a chat session with the previous messages
    chat = model.start_chat(history=chat_history_for_api)

    # Send the latest message and get the model's response
    response = chat.send_message(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response.text)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response.text})
