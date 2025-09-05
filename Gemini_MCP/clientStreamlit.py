# import asyncio
# import json
# import sys
# from typing import Optional
# from contextlib import AsyncExitStack
# from subprocess import run, PIPE

# import streamlit as st
# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client

# # This is a hardcoded path for demonstration purposes.
# # In a real-world app, you might make this configurable via a text input field.
# SETTINGS_FILE = r"C:\Users\Anish\.gemini\settings.json"

# class MCPClient:
#     def __init__(self):
#         """Initialize the MCP client with Gemini CLI support"""
#         self.session: Optional[ClientSession] = None
#         self.exit_stack = AsyncExitStack()
#         self.settings_file = SETTINGS_FILE

#     async def connect_to_server(self, server_script_path: str):
#         """Connect to an MCP server and register it with Gemini MCP"""
#         is_python = server_script_path.endswith(".py")
#         is_js = server_script_path.endswith(".js")
#         if not (is_python or is_js):
#             raise ValueError("Server script must be a .py or .js file")

#         command = "python" if is_python else "node"
#         server_params = StdioServerParameters(
#             command=command,
#             args=[server_script_path],
#             env=None
#         )

#         stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
#         self.stdio, self.write = stdio_transport
#         self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

#         await self.session.initialize()

#         # List available tools
#         response = await self.session.list_tools()
#         tools = response.tools
#         st.write("Connected to server with tools:", [tool.name for tool in tools])

#         # Register MCP server in settings.json
#         await self.register_mcp_server("weather_server", server_script_path, tools)

#     async def register_mcp_server(self, server_name: str, server_script_path: str, tools: list):
#         """Register or update MCP server configuration in settings.json"""
#         try:
#             with open(self.settings_file, "r") as f:
#                 settings = json.load(f)
#         except (FileNotFoundError, json.JSONDecodeError):
#             settings = {}

#         mcp_servers = settings.get("mcpServers", {})

#         is_python = server_script_path.endswith(".py")
#         command = "python" if is_python else "node"

#         mcp_servers[server_name] = {
#             "command": command,
#             "args": [server_script_path],
#             "env": {},
#             "cwd": ".",
#             "timeout": 30000,
#             "trust": False,
#             "includeTools": [tool.name for tool in tools]
#         }

#         settings["mcpServers"] = mcp_servers

#         with open(self.settings_file, "w") as f:
#             json.dump(settings, f, indent=2)

#         st.write(f"MCP server '{server_name}' registered in {self.settings_file}")

#     def call_gemini(self, prompt: str) -> str:
#         """Call Gemini CLI with a given prompt"""
#         result = run(["gemini", "-p", prompt], stdout=PIPE, stderr=PIPE, text=True, shell=True)
#         if result.returncode != 0:
#             return f"[Gemini Error] {result.stderr.strip()}"
#         return result.stdout.strip()

#     async def process_query(self, query: str) -> str:
#         """Process a user query using Gemini CLI"""
#         st.session_state.messages.append({"role": "user", "content": query})
        
#         with st.chat_message("user"):
#             st.write(query)

#         with st.chat_message("assistant"):
#             with st.spinner("Thinking..."):
#                 try:
#                     gemini_response = self.call_gemini(query)
#                     st.write(gemini_response)
#                     st.session_state.messages.append({"role": "assistant", "content": gemini_response})
#                     return gemini_response
#                 except Exception as e:
#                     error_message = f"An error occurred: {e}"
#                     st.error(error_message)
#                     st.session_state.messages.append({"role": "assistant", "content": error_message})
#                     return error_message


# # --- Streamlit App ---

# st.set_page_config(page_title="MCP Gemini Chat", layout="wide")
# st.title("MCP Gemini Chat")

# # Initialize session state for the client and chat history
# if "client_state" not in st.session_state:
#     st.session_state.client_state = None
#     st.session_state.messages = []

# # Get server path from command-line arguments
# try:
#     if len(sys.argv) < 2:
#         st.error("Error: Server script path not provided.")
#         st.info("Usage: streamlit run app.py -- <path_to_server_script>")
#         st.stop()
#     server_path = sys.argv[1]

#     # If not connected, connect automatically on startup
#     if st.session_state.client_state is None:
#         with st.spinner("Connecting to MCP server..."):
#             client = MCPClient()
#             asyncio.run(client.connect_to_server(server_path))
#             st.session_state.client_state = client
#             st.success("Successfully connected to the MCP server!")
#             st.session_state.messages.append({"role": "assistant", "content": "Hello! I am connected and ready to chat."})
# except Exception as e:
#     st.error(f"Failed to connect: {e}")
#     st.stop()


# # If connected, show the chat interface
# st.success("Connected to MCP server. Start chatting below!")

# for msg in st.session_state.messages:
#     with st.chat_message(msg["role"]):
#         st.write(msg["content"])

# if prompt := st.chat_input("Enter your query..."):
#     # Use asyncio.run to execute the async method
#     asyncio.run(st.session_state.client_state.process_query(prompt))

# # A button to disconnect and reset the app state
# if st.button("Disconnect and Reset"):
#     asyncio.run(st.session_state.client_state.cleanup())
#     st.session_state.client_state = None
#     st.session_state.messages = []
#     st.rerun()

import asyncio
import json
import sys
from typing import Dict, List, Optional
from pathlib import Path
from contextlib import AsyncExitStack
from subprocess import run, PIPE

import streamlit as st
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Path to Gemini CLI settings
SETTINGS_FILE = r"C:\Users\Anish\.gemini\settings.json"


def server_name_from_path(p: str) -> str:
    """Use the script filename (without extension) as the server name."""
    return Path(p).stem


class MCPClient:
    def __init__(self):
        """Initialize the MCP client with multi-server support."""
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self.settings_file = SETTINGS_FILE

    async def connect_to_servers(self, server_script_paths: List[str]):
        """Connect to all MCP servers and register them in Gemini MCP settings."""
        servers_info = []  # collect info to register in settings.json

        for server_script_path in server_script_paths:
            is_python = server_script_path.endswith(".py")
            is_js = server_script_path.endswith(".js")
            if not (is_python or is_js):
                raise ValueError(f"Server script must be a .py or .js file: {server_script_path}")

            command = "python" if is_python else "node"
            server_name = server_name_from_path(server_script_path)

            server_params = StdioServerParameters(
                command=command,
                args=[server_script_path],
                env=None
            )

            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            stdio, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))

            await session.initialize()

            # List available tools for this server
            resp = await session.list_tools()
            tools = resp.tools
            tool_names = [t.name for t in tools]

            # Store the session by server name
            self.sessions[server_name] = session

            st.write(f"✅ Connected to **{server_name}** with tools: {tool_names or '[none]'}")

            servers_info.append({
                "name": server_name,
                "path": server_script_path,
                "command": command,
                "includeTools": tool_names,
            })

        # Register/update all servers in settings.json
        self._register_mcp_servers(servers_info)

    def _register_mcp_servers(self, servers_info: List[dict]):
        """Merge multiple server entries into settings.json -> mcpServers."""
        try:
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            settings = {}

        mcp_servers = settings.get("mcpServers", {})

        for info in servers_info:
            name = info["name"]
            path = info["path"]
            command = info["command"]
            include_tools = info["includeTools"]

            # Merge/update this server entry
            mcp_servers[name] = {
                "command": command,
                "args": [path],
                "env": {},
                "cwd": ".",
                "timeout": 30000,
                "trust": False,
                "includeTools": include_tools,
            }

        settings["mcpServers"] = mcp_servers

        with open(self.settings_file, "w") as f:
            json.dump(settings, f, indent=2)

        st.write(f"📝 Registered/updated MCP servers in {self.settings_file}: **{list(mcp_servers.keys())}**")

    def call_gemini(self, prompt: str) -> str:
        """Call Gemini CLI with a given prompt (kept intact from your original)."""
        result = run(["gemini", "-p", prompt], stdout=PIPE, stderr=PIPE, text=True, shell=True)
        if result.returncode != 0:
            return f"[Gemini Error] {result.stderr.strip()}"
        return result.stdout.strip()

    async def process_query(self, query: str) -> str:
        """Process a user query using Gemini CLI (chat UI behavior unchanged)."""
        st.session_state.messages.append({"role": "user", "content": query})

        with st.chat_message("user"):
            st.write(query)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    gemini_response = self.call_gemini(query)
                    st.write(gemini_response)
                    st.session_state.messages.append({"role": "assistant", "content": gemini_response})
                    return gemini_response
                except Exception as e:
                    error_message = f"An error occurred: {e}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
                    return error_message

    async def cleanup(self):
        """Clean up resources (close all sessions)."""
        await self.exit_stack.aclose()


# --- Streamlit App ---

st.set_page_config(page_title="MCP Gemini Chat (Multi-Server)", layout="wide")
st.title("MCP Gemini Chat (Multi-Server)")

# Initialize session state
if "client_state" not in st.session_state:
    st.session_state.client_state: Optional[MCPClient] = None
    st.session_state.messages = []

try:
    if len(sys.argv) < 2:
        st.error("Error: No server script paths provided.")
        st.info("Usage: streamlit run client.py -- <path_to_server1> <path_to_server2> ...")
        st.stop()

    server_paths = sys.argv[1:]

    # Connect once on first load
    if st.session_state.client_state is None:
        async def init_all():
            with st.spinner("Connecting to MCP servers..."):
                client = MCPClient()
                await client.connect_to_servers(server_paths)
                st.session_state.client_state = client
                st.success("Successfully connected to all MCP servers!")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Hello! All specified MCP servers are connected and registered."
                })

        asyncio.run(init_all())

except Exception as e:
    st.error(f"Failed to connect: {e}")
    st.stop()

# Chat interface
if st.session_state.client_state:
    st.success("Connected. Start chatting below!")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Enter your query..."):
        async def run_query():
            await st.session_state.client_state.process_query(prompt)

        asyncio.run(run_query())

    if st.button("Disconnect and Reset"):
        async def cleanup_client():
            await st.session_state.client_state.cleanup()
            st.session_state.client_state = None
            st.session_state.messages = []
        asyncio.run(cleanup_client())
        st.rerun()
