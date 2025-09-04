import streamlit as st
import subprocess
import sys

# Since Docker is no longer being used, the CONTAINER_ID is not needed.
# We will run the gemini command directly on the host machine.

def run_gemini_cli(user_prompt):
    """
    Executes the Gemini CLI directly on the local machine with the given prompt.

    Args:
        user_prompt (str): The prompt to send to the Gemini CLI.

    Returns:
        str: The output from the Gemini CLI, or an error message.
    """
    try:
        # Construct the full command to execute.
        # We use "-p" for non-interactive mode as per the README.md file.
        command = [
            'gemini',
            '-p',
            user_prompt
        ]

        # Use subprocess.run to execute the command and capture the output.
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            shell=True
        )

        return result.stdout.strip()

    except subprocess.CalledProcessError as e:
        # This handles errors from the gemini command itself.
        return f"Error executing Gemini CLI: {e.stderr}"
    except FileNotFoundError as e:
        # This handles cases where the 'gemini' command is not found.
        return e

# --- Streamlit UI Setup ---

st.set_page_config(page_title="Gemini Chat", layout="centered")

st.title("Gemini CLI Interface")
st.markdown("Interact with the Gemini CLI")

# Initialize chat history in Streamlit's session state
if "messages" not in st.session_state:
    st.session_state.messages = []

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

    # Display a loading indicator while the response is being generated
    with st.spinner("Sending prompt to Gemini CLI..."):
        # Run the command and get the response
        response = run_gemini_cli(prompt)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
