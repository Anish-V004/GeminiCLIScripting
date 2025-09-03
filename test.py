import subprocess

def run_gemini_in_docker(container_id, user_prompt):
    try:
        # Construct the full command to execute inside the container.
        # We're using `sh -c` to allow the prompt to be passed as a single string.
        # This assumes the `gemini` executable is in the container's PATH.
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

if __name__ == '__main__':
    # Prompt the user for the container ID or name.
    container_id = "3568825b96edf2f00baa3f57716c604a63f7c161628760cc7b6616cc5c55ea2b"
 
    print("\n----------------------------------------------------")
    print("Docker-to-Gemini bridge active. Type 'exit' to quit.")
    print("----------------------------------------------------\n")
    
    while True:
        try:
            # Prompt the user for the input prompt.
            prompt = input("Your prompt for Gemini: ").strip()
            
            if prompt.lower() == 'exit':
                print("Exiting.")
                break
            
            if not prompt:
                print("Prompt cannot be empty. Please try again.")
                continue
            
            # Run the command and get the response.
            print("Sending prompt to Gemini CLI...")
            response = run_gemini_in_docker(container_id, "-p "+prompt)
            
            # Print the response.
            print("\n----------------------")
            print("Response from Gemini:")
            print("----------------------")
            print(response)
            print("----------------------\n")
            
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully.
            print("\nExiting.")
            break
