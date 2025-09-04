# import asyncio
# import json
# import sys
# from typing import Optional
# from contextlib import AsyncExitStack
# from subprocess import run, PIPE

# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client


# class MCPClient:
#     def __init__(self, settings_file: str = r"C:\Users\Anish\.gemini\settings.json"):
#         """Initialize the MCP client with Gemini CLI support"""
#         self.session: Optional[ClientSession] = None
#         self.exit_stack = AsyncExitStack()
#         self.settings_file = settings_file

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
#         print("\nConnected to server with tools:", [tool.name for tool in tools])

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

#         print(f"\nMCP server '{server_name}' registered in {self.settings_file}")

#     def call_gemini(self, prompt: str) -> str:
#         """Call Gemini CLI with a given prompt"""
#         result = run(["gemini", "-p", prompt], stdout=PIPE, stderr=PIPE, text=True, shell=True)
#         if result.returncode != 0:
#             return f"[Gemini Error] {result.stderr.strip()}"
#         return result.stdout.strip()

#     async def process_query(self, query: str) -> str:
#         """Process a user query using Gemini CLI"""
#         print("[DEBUG] Query received:", query)

#         gemini_response = self.call_gemini(query)
#         print("[DEBUG] Gemini response:", gemini_response)

#         return gemini_response

#     async def chat_loop(self):
#         """Run an interactive chat loop"""
#         print("\nMCP Client with Gemini Started!")
#         print("Type your queries or 'quit' to exit.")

#         while True:
#             try:
#                 query = input("\nQuery: ").strip()
#                 if query.lower() == "quit":
#                     break

#                 response = await self.process_query(query)
#                 print("\n" + response)

#             except Exception as e:
#                 print(f"\nError: {str(e)}")

#     async def cleanup(self):
#         """Clean up resources"""
#         await self.exit_stack.aclose()


# async def main():
#     if len(sys.argv) < 2:
#         print("Usage: python client.py <path_to_server_script>")
#         sys.exit(1)

#     client = MCPClient()
#     try:
#         await client.connect_to_server(sys.argv[1])
#         await client.chat_loop()
#     finally:
#         await client.cleanup()


# if __name__ == "__main__":
#     asyncio.run(main())

import asyncio
import json
import sys
from typing import Dict, List, Optional
from pathlib import Path
from contextlib import AsyncExitStack
from subprocess import run, PIPE
from datetime import datetime

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Path to Gemini CLI settings
SETTINGS_FILE = r"C:\Users\Anish\.gemini\settings.json"


def log(message: str, level: str = "INFO"):
    """Prints a log message with timestamp and level inline in chat."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def server_name_from_path(p: str) -> str:
    return Path(p).stem


class MCPClient:
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self.settings_file = SETTINGS_FILE

    async def connect_to_servers(self, server_script_paths: List[str]):
        log("Starting connection to MCP servers...")
        servers_info = []

        for server_script_path in server_script_paths:
            is_python = server_script_path.endswith(".py")
            is_js = server_script_path.endswith(".js")
            if not (is_python or is_js):
                log(f"Invalid server script: {server_script_path}", "ERROR")
                raise ValueError(f"Server script must be a .py or .js file: {server_script_path}")

            command = "python" if is_python else "node"
            server_name = server_name_from_path(server_script_path)

            log(f"Connecting to server: {server_name} ({server_script_path})")
            server_params = StdioServerParameters(command=command, args=[server_script_path], env=None)

            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            stdio, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))

            await session.initialize()
            log(f"Initialized session for {server_name}")

            resp = await session.list_tools()
            tools = resp.tools
            tool_names = [t.name for t in tools]
            log(f"Available tools for {server_name}: {tool_names or '[none]'}")

            self.sessions[server_name] = session

            servers_info.append({
                "name": server_name,
                "path": server_script_path,
                "command": command,
                "includeTools": tool_names,
            })

        self._register_mcp_servers(servers_info)

    def _register_mcp_servers(self, servers_info: List[dict]):
        log("Registering MCP servers in settings.json...")
        try:
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            log("No valid settings.json found, creating a new one.", "WARNING")
            settings = {}

        mcp_servers = settings.get("mcpServers", {})

        for info in servers_info:
            mcp_servers[info["name"]] = {
                "command": info["command"],
                "args": [info["path"]],
                "env": {},
                "cwd": ".",
                "timeout": 30000,
                "trust": False,
                "includeTools": info["includeTools"],
            }

        settings["mcpServers"] = mcp_servers

        with open(self.settings_file, "w") as f:
            json.dump(settings, f, indent=2)

        log(f"Updated settings.json with servers: {list(mcp_servers.keys())}")

    def call_gemini(self, prompt: str) -> str:
        log(f"Calling Gemini CLI with prompt: {prompt}")
        result = run(["gemini", "-p", prompt], stdout=PIPE, stderr=PIPE, text=True, shell=True)
        if result.returncode != 0:
            log(f"Gemini Error: {result.stderr.strip()}", "ERROR")
            return f"[Gemini Error] {result.stderr.strip()}"
        log("Gemini response received successfully")
        return result.stdout.strip()

    async def process_query(self, query: str) -> str:
        log(f"Processing user query: {query}")
        try:
            response = self.call_gemini(query)
            log(f"Final response: {response}")
            print(f"\n[Assistant] {response}")
            return response
        except Exception as e:
            log(f"Error processing query: {e}", "ERROR")
            return f"[Error] {e}"

    async def cleanup(self):
        log("Cleaning up MCP client sessions...")
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server1> <path_to_server2> ...")
        sys.exit(1)

    server_paths = sys.argv[1:]
    client = MCPClient()
    await client.connect_to_servers(server_paths)

    log("MCP Gemini Chat started. Type 'exit' to quit.")
    print("\n[MCP Gemini Chat] Type your messages below. Type 'exit' or 'quit' to disconnect.")

    try:
        while True:
            query = input("\n> ")
            if query.strip().lower() in {"exit", "quit"}:
                break
            await client.process_query(query)
    finally:
        await client.cleanup()
        log("Disconnected from all servers.")


if __name__ == "__main__":
    asyncio.run(main())
