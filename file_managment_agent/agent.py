import os
import re
import string
import platform
import subprocess
from dotenv import load_dotenv

load_dotenv()

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams,
    StdioServerParameters,
)

# # ------------------------
# # Dynamic Drive Detection
# # ------------------------
def get_available_roots():
    system = platform.system().lower()
    print(f"[DEBUG] Detecting drives on system: {system}")
    if system == "windows":
        drives = []
        for letter in string.ascii_uppercase:
            root = f"{letter}:/"
            if os.path.exists(root):
                drives.append(root)
        return drives

    # Linux / macOS
    roots = ['/']
    for extra in ['/mnt', '/media', '/Volumes']:
        if os.path.exists(extra):
            roots.append(extra)

    return roots



def create_filesystem_agent(root_path):
    """Create an MCP-enabled filesystem agent for a specific root."""
    root_path = os.path.abspath(root_path)
    drives = get_available_roots()
    print(f"[INFO] Available drives: {drives}")
    
    if not os.path.exists(root_path):
        raise RuntimeError(f"[ERROR] Root path does not exist: {root_path}")

    print(f"[INFO] Launching MCP server on: {root_path}")

    return LlmAgent(
        model="gemini-2.0-flash",
        name="fs_agent",
        instruction="""
        You are a smart file explorer.
        - If user gives a full path → use it directly.
        - If user says "open ML file" → search files.
        - If the file is on another drive → Detect and request root switch.
        """,
        tools=[
            McpToolset(
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command="npx",
                        args=[
                            "-y",
                            "@modelcontextprotocol/server-filesystem",
                            root_path,
                            *drives
                        ],
                    ),
                    # timeout=60,
                )
            )
        ],
    )


# First ensure root_path.txt exists
DEFAULT_ROOT = os.path.abspath(os.path.dirname(__file__))
root_agent = create_filesystem_agent(DEFAULT_ROOT)

print(f"[ADK] File system agent mounted at: {DEFAULT_ROOT}")
