import streamlit as st
import subprocess
import sys

# Define the container ID as a constant, as you provided.
CONTAINER_ID = "3568825b96edf2f00baa3f57716c604a63f7c161628760cc7b6616cc5c55ea2b"

def run_gemini_in_docker(container_id, user_prompt):
    """
    Executes the Gemini CLI inside a running Docker container with the given prompt.
    This function is a direct copy of your provided logic.

    Args:
        container_id (str): The name or ID of the running Docker container.
        user_prompt (str): The prompt to send to the Gemini CLI.

    Returns:
        str: The output from the Gemini CLI, or an error message.
    """
    try:
        # Construct the full command to execute inside the container.
        command_in_container = f"gemini '{user_prompt}'"

        # The `docker exec` command to run from the host.
        docker_command = [
            'docker',
            'exec',
            container_id,
            '/bin/sh',
            '-c',
            command_in_container
        ]

        # Use subprocess.run to execute the command and capture the output.
        result = subprocess.run(
            docker_command,
            capture_output=True,
            text=True,
            check=True
        )

        return result.stdout.strip()

    except subprocess.CalledProcessError as e:
        # This handles errors from the docker command itself.
        return f"Error executing command in Docker container: {e.stderr}"
    except FileNotFoundError:
        # This handles cases where the 'docker' command is not in the system's PATH.
        return "Error: 'docker' command not found. Please ensure Docker is installed and in your PATH."

# --- Streamlit UI Setup ---

st.set_page_config(page_title="Dockerized Gemini Chat", layout="centered")

st.title("Dockerized Gemini CLI Interface")
st.markdown("Interact with the Gemini CLI running inside your Docker container.")

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
        response = run_gemini_in_docker(CONTAINER_ID, "-p " + prompt)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)

