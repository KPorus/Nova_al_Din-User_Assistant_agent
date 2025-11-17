# import os
# import string
# from dotenv import load_dotenv

# load_dotenv()

# from google.adk.agents import LlmAgent
# from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
# from google.adk.tools.mcp_tool.mcp_session_manager import (
#     StdioConnectionParams,
#     StdioServerParameters,
# )

# # -----------------------------------
# # CONSTANTS
# # -----------------------------------
# NPX_PATH = r"C:\nvm4w\nodejs\npx.cmd"


# # -----------------------------------
# # DRIVE DETECTION
# # -----------------------------------

# def get_available_windows_drives():
#     """Detect all mounted drives like C:/, D:/, G:/."""
#     return [
#         f"{letter}:/"
#         for letter in string.ascii_uppercase
#         if os.path.exists(f"{letter}:/")
#     ]


# # -----------------------------------
# # MCP FILESYSTEM AGENT
# # -----------------------------------

# def create_filesystem_agent():
#     """Create MCP filesystem agent with full drive access."""
#     drives = get_available_windows_drives()
#     if not drives:
#         raise RuntimeError("No drives detected on this system.")

#     print(f"[INFO] Mounting drives: {drives}")

#     # Use C drive as the root (required by MCP), but also mount all others
#     root_path = drives[0]

#     return LlmAgent(
#         model="gemini-2.0-flash",
#         name="fs_agent",
#         instruction="""
#         You are a smart file explorer.
#         - You have full access to all drives.
#         - If user gives a full path → open it.
#         - If user says "search ML folder" → scan all drives.
#         """,
#         tools=[
#             McpToolset(
#                 connection_params=StdioConnectionParams(
#                     server_params=StdioServerParameters(
#                         command="npx",
#                         args=[
#                             "-y",
#                             "@modelcontextprotocol/server-filesystem",
#                             root_path,  # required root
#                             *drives     # mount all drives
#                         ],
#                     ),
#                 )
#             )
#         ],
#     )


# # -----------------------------------
# # CREATE AGENT
# # -----------------------------------

# file_agent = create_filesystem_agent()
# print("[ADK] Filesystem agent is ready with full drive access.")


# import os
# import re
# import string
# import platform
# import subprocess
# from dotenv import load_dotenv

# load_dotenv()

# from google.adk.agents import LlmAgent
# from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
# from google.adk.tools.mcp_tool.mcp_session_manager import (
#     StdioConnectionParams,
#     StdioServerParameters,
# )
# from google.adk.tools.function_tool import FunctionTool

# NPX_PATH = r"C:\nvm4w\nodejs\npx.cmd"
# ROOT_FILE = os.path.join(os.path.dirname(__file__), "root_path.txt")

# # ---------------------------
# # Utility functions
# # ---------------------------

# def load_root():
#     if not os.path.exists(ROOT_FILE):
#         return None
#     return open(ROOT_FILE).read().strip()

# def save_root(path):
#     with open(ROOT_FILE, "w") as f:
#         f.write(path)
#     print("[ROOT] Updated to:", path)

# def detect_drive(msg: str):
#     msg = msg.lower()
#     m = re.match(r"([a-z]:)", msg)
#     if m:
#         return m.group(1).upper() + ":/"

#     for letter in string.ascii_uppercase:
#         patterns = [
#             f"{letter.lower()} drive",
#             f"{letter.lower()}:",
#             f"go to {letter.lower()}:",
#             f"open {letter.lower()}",
#         ]
#         if any(p in msg for p in patterns):
#             return f"{letter}:/"
#     return None


# # ---------------------------
# # MCP Root Manager with Full Restart
# # ---------------------------

# class RootManager:
#     def __init__(self):
#         self.current_root = load_root() or "G:/"  # default
#         self._toolset = None
#         self._restart_toolset()

#     def _restart_toolset(self):
#         """Fully restart MCP server with new root"""
#         root = self.current_root

#         # CRITICAL: Allow full drive access
#         # Use the drive root (e.g., D:/) and allow all subpaths
#         server_params = StdioServerParameters(
#             command=NPX_PATH,
#             args=[
#                 "-y",
#                 "@modelcontextprotocol/server-filesystem",
#                 root,                     # ← Root directory (e.g., D:/)
#                 "--allow", "root",          # ← Explicitly allow this path
#                 "--allow-children-of", root,  # ← Allow all subdirectories
#             ],
#             cwd=os.path.dirname(root) if len(root) == 3 else root  # e.g., D:/
#         )

#         connection_params = StdioConnectionParams(
#             server_params=server_params,
#             timeout=60,
#         )

#         self._toolset = McpToolset(connection_params=connection_params)
#         print(f"[MCP RESTARTED] Root: {root}")

#     def get_toolset(self):
#         return self._toolset

#     def switch_drive(self, drive: str):
#         new_root = drive.upper()  # e.g., "D:/"
#         if new_root == self.current_root:
#             return {"status": "NO_CHANGE", "root": new_root}

#         print(f"[ROOT SWITCH] Changing from {self.current_root} → {new_root}")
#         save_root(new_root)
#         self.current_root = new_root
#         self._restart_toolset()  # ← FULL RESTART

#         return {"status": "OK", "root": new_root, "message": f"Switched to {new_root}"}


# # Initialize
# root_mgr = RootManager()


# # ---------------------------
# # TOOL: switch_root
# # ---------------------------

# def tool_switch_root(drive: str):
#     """
#     Switch filesystem root to another drive (e.g., D:/).
#     Restarts MCP server with full access to the new drive.
#     """
#     if not drive.endswith(":/"):
#         drive = drive.upper() + ":/"

#     result = root_mgr.switch_drive(drive)
#     return result


# switch_root_tool = FunctionTool(
#     func=tool_switch_root,
#     # name="switch_root",
#     # description="""
#     # Switch the active filesystem root to a different drive.
#     # Use when user says: 'open D drive', 'go to E:', 'files in F:/folder', etc.
#     # Input: drive letter with colon and slash, e.g., 'D:/'
#     # """,
# )


# # ---------------------------
# # LLM Agent
# # ---------------------------

# root_agent = LlmAgent(
#     model="gemini-2.0-flash",
#     name="fs_agent",
#     instruction="""
# You are a smart file explorer with full access to the current drive.

# • Detect drive changes in user input:
#   - 'open D drive' → call switch_root("D:/")
#   - 'file in E:/data' → call switch_root("E:/")
#   - 'go to G:\\projects' → call switch_root("G:/")

# • After switching:
#   - You now have full read/write access to ALL folders on that drive.
#   - List, create, read, edit, delete files normally.

# • Current root is updated automatically after switch.
# """,
#     tools=[
#         switch_root_tool,
#         root_mgr.get_toolset(),  # ← Fresh toolset with full drive access
#     ],
# )

# print("[AGENT READY] Root mounted at:", root_mgr.current_root)


# import os
# import re
# import string
# import platform
# from dotenv import load_dotenv

# # ------------------------
# # ENVIRONMENT
# # ------------------------
# load_dotenv()
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# print("✅ Gemini API key loaded" if GOOGLE_API_KEY else "❌ Missing API key")

# # ------------------------
# # ADK IMPORTS (Correct versions)
# # ------------------------
# from google.adk.agents import LlmAgent
# from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
# from google.adk.tools.mcp_tool.mcp_session_manager import (
#     StdioConnectionParams,
#     StdioServerParameters,   # <-- correct ADK import
# )

# # ------------------------
# # ROOT DIRECTORY (SAFE)
# # ------------------------
# # Absolute required! Prevents MCP crash.
# global BASE_DIR
# try:
#     base_path = os.path.abspath(os.path.dirname(__file__))
#     BASE_DIR = base_path
# except NameError:
#     # Fallback in interactive environments like notebooks
#     base_path = os.path.abspath((os.getcwd()))
#     BASE_DIR = base_path

# # os.makedirs(base_path, exist_ok=True)

# # BASE_DIR = os.path.abspath(
# #     os.path.join(os.path.dirname(__file__), "workspace")
# # )
# # os.makedirs(BASE_DIR, exist_ok=True)

# print(f"📁 MCP Root Directory: {BASE_DIR} (Exists: {os.path.exists(BASE_DIR)})")

# # ------------------------
# # Dynamic Drive Detection
# # ------------------------
# def get_available_roots():
#     system = platform.system().lower()

#     if system == "windows":
#         drives = []
#         for letter in string.ascii_uppercase:
#             root = f"{letter}:/"
#             if os.path.exists(root):
#                 drives.append(root)
#         return drives

#     # Linux / macOS
#     roots = ['/']
#     for extra in ['/mnt', '/media', '/Volumes']:
#         if os.path.exists(extra):
#             roots.append(extra)

#     return roots

# # ------------------------
# # Search File by Keyword
# # ------------------------
# def find_file_by_guess(keyword, roots):
#     keyword = keyword.lower()

#     for root in roots:
#         for dirpath, _, filenames in os.walk(root):
#             for file in filenames:
#                 if keyword in file.lower():
#                     return os.path.join(dirpath, file)

#     return None

# # ------------------------
# # Extract Path or Keyword
# # ------------------------
# def extract_path_or_keyword(user_message):
#     windows = re.findall(r"[A-Za-z]:\\[^\s]+", user_message)
#     linux = re.findall(r"(\/[\w\/\.\-]+|\.[\w\/\.\-]+)", user_message)

#     if windows:
#         return windows[0], True
#     if linux:
#         return linux[0], True

#     return user_message.strip().lower(), False

# # ------------------------
# # Determine Root for Path
# # ------------------------
# def get_root_for_path(path):
#     if ":" in path:       # Windows drive
#         return path.split("\\")[0] + "/"

#     if path.startswith("/"):   # Linux root
#         return "/"

#     return BASE_DIR

# # ------------------------
# # Create MCP Filesystem Agent
# # ------------------------
# def create_filesystem_agent(root_path):
#     # Convert to absolute path to avoid MCP crash
#     root_path = os.path.abspath(root_path)
#     print(f"Creating filesystem agent with root: {root_path}")

#     # Path to the locally installed MCP server
#     mcp_server_path = os.path.join(
#         root_path,
#         "node_modules",
#         "@modelcontextprotocol",
#         "server-filesystem",
#         "dist",
#         "index.js"
#     )

#     if not os.path.exists(mcp_server_path):
#         raise FileNotFoundError(
#             f"MCP server not found at:\n{mcp_server_path}\n\n"
#             "Run this in your agent folder:\n"
#             "  cd G:\\ML\\File_system_agent\\file_managment_agent\n"
#             "  npm install @modelcontextprotocol/server-filesystem"
#         )
    
#     return LlmAgent(
#         model="gemini-2.0-flash",
#         name="filesystem_agent",
#         instruction="""
# You are a robust filesystem assistant.
# The user will speak naturally (e.g., "open the ML file").
# You will:

# 1. Detect whether they gave a full path or just a keyword.
# 2. If keyword → search all drives for closest match.
# 3. Mount the MCP filesystem server at correct root.
# 4. Use list_directory and read_file to show file contents.
# """,
#         tools=[
#             McpToolset(
#                 connection_params=StdioConnectionParams(
#                     server_params=StdioServerParameters(
#                         command=r"C:\nvm4w\nodejs\node.exe",  # Direct node
#                         args=[
#                             mcp_server_path,
#                             root_path
#                         ],
#                     ),
#                     timeout=60,
#                 )
#             )
#         ],
#     )

# # ------------------------
# # ADK REQUIRED VARIABLE
# # ------------------------
# # This MUST exist. ADK reads ONLY this variable.
# root_agent = create_filesystem_agent(BASE_DIR)
# print(BASE_DIR)
# print("Filesystem agent created.", root_agent)


# import os
# import re
# import string
# import platform
# import uuid
# from google.genai import types

# from google.adk.agents import LlmAgent
# from google.adk.models.google_llm import Gemini
# from google.adk.runners import Runner
# from google.adk.sessions import InMemorySessionService

# from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
# from google.adk.tools.tool_context import ToolContext
# from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams

# from mcp import StdioServerParameters

# from google.adk.apps.app import App, ResumabilityConfig
# from google.adk.tools.function_tool import FunctionTool


# from dotenv import load_dotenv

# load_dotenv()  # loads variables from .env
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# if GOOGLE_API_KEY:
#     print("✅ Gemini API key setup complete.")
# else:
#     print("❌ GOOGLE_API_KEY not found.")
    
# session_service = InMemorySessionService()
# def get_available_roots():
#     system = platform.system().lower()

#     # Windows: detect drives (C:, D:, E:, ...)
#     if system == "windows":
#         drives = []
#         for letter in string.ascii_uppercase:
#             drive = f"{letter}:/"
#             if os.path.exists(drive):
#                 drives.append(drive)
#         print(f"Detected drives: {drives}")
#         return drives

#     # Linux/macOS: treat / as the root
#     else:
#         roots = ['/']
#         # Optional: scan /mnt, /media, /Volumes
#         for extra in ['/mnt', '/media', '/Volumes']:
#             if os.path.exists(extra):
#                 roots.append(extra)
#         return roots



# def find_file_by_guess(keyword, roots):
#     keyword = keyword.lower()

#     for root in roots:
#         for dirpath, _, filenames in os.walk(root):
#             for f in filenames:
#                 if keyword in f.lower():
#                     return os.path.join(dirpath, f)
#     return None



# def extract_path_or_keyword(user_message):
#     # Full path Windows (C:\folder\file.py)
#     windows = re.findall(r"[A-Za-z]:\\[^\s]+", user_message)

#     # Linux paths (/root/folder/file)
#     linux = re.findall(r"(\/[\w\/\.\-]+|\.[\w\/\.\-]+)", user_message)

#     if windows:
#         return windows[0], True
#     if linux:
#         return linux[0], True
    
#     # Otherwise treat as keyword for guessing
#     return user_message.strip().lower(), False


# def get_root_for_path(path):
#     # Windows root like "D:/"
#     if ":" in path:
#         return path.split("\\")[0] + "/"
#     # Linux root "/"
#     if path.startswith("/"):
#         return "/"
#     # fallback
#     return "./"


# # def create_filesystem_agent(root_path):
# #     return LlmAgent(
# #         model="gemini-2.0-flash-lite",
# #         name="fs_agent",
# #         instruction="Find and open files naturally.",
# #         tools=[
# #             McpToolset(
# #                 connection_params=StdioConnectionParams(
# #                     server_params=StdioServerParameters(
# #                         command="npx",
# #                         args=[
# #                             "-y",
# #                             "@modelcontextprotocol/server-filesystem",
# #                             root_path
# #                         ],
# #                     ),
# #                     timeout=30,
# #                 )
# #             )      
# #         ]
# #     )


# # === CRITICAL: Use full path to npx.cmd from nvm-windows ===
# NPX_PATH = r"C:\nvm4w\nodejs\npx.cmd"

# # === Root directory (absolute) ===
# ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
# print(f"MCP Root: {ROOT_DIR}")

# def create_filesystem_agent(root_path):
#     root_path = os.path.abspath(root_path)
#     print(f"Launching MCP server with npx: {NPX_PATH}")

#     return LlmAgent(
#         model="gemini-2.0-flash",  # Valid model
#         name="fs_agent",
#         instruction="""
#         You are a smart file explorer.
#         - If user gives a full path → use it directly.
#         - If user says "find ML file" → search for matching files.
#         - Use list_directory and read_file tools.
#         """,
#         tools=[
#             McpToolset(
#                 connection_params=StdioConnectionParams(
#                     server_params=StdioServerParameters(
#                         command=NPX_PATH,  # ← FULL PATH!
#                         args=[
#                             "-y",
#                             "@modelcontextprotocol/server-filesystem",
#                             root_path
#                         ],
#                     ),
#                     timeout=60,
#                 )
#             )
#         ],
#     )

# # === Create agent ===
# root_agent = create_filesystem_agent(ROOT_DIR)
# print("Filesystem agent created successfully!")