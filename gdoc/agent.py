from google.adk.agents import Agent
from google.genai import types
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from gdoc.list_doc import list_my_google_docs, find_document_by_title
from gdoc.share_doc import share_google_doc, get_doc_permissions, update_doc_permission
from gdoc.doc_creation import resolve_ambiguity, docs_operation, create_google_doc
from gdoc.doc_deletion import delete_google_doc
# # ============================================================
# # GEMINI RETRY POLICY
# # ============================================================
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504]
)


# =============================================================================
# 1. Authentication
# =============================================================================

# KEYFILE_PATH = os.getcwd() + "/gdoc/credentials/oauth.keys.json"
# GDRIVE_CREDENTIALS_PATH = os.getcwd() + "/gdoc/credentials/.gdrive-server-credentials.json"
# GDOC_CREDENTIALS_PATH = os.getcwd() + "/gdoc/credentials/.gdoc-server-credentials.json"
# DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
# PORT = 8080
# SCOPES = [
#     'https://www.googleapis.com/auth/documents',
# ]

# def get_docs_service():
#     authenticate_and_save("docs")
#     creds = Credentials.from_authorized_user_file(GDOC_CREDENTIALS_PATH, SCOPES)
#     return build('docs', 'v1', credentials=creds)

# def get_drive_service():
#     authenticate_and_save("drive")
#     creds = Credentials.from_authorized_user_file(GDRIVE_CREDENTIALS_PATH, DRIVE_SCOPES)
#     return build("drive", "v3", credentials=creds)

# def authenticate_and_save(app: str = "drive"):
    
#     if(app == "drive"):
#         if os.path.exists(GDRIVE_CREDENTIALS_PATH):
#             return
#         creds = None
#         if not creds or not creds.valid:
#             if creds and creds.expired and creds.refresh_token:
#                 try:
#                     creds.refresh(Request())
#                 # Save the refreshed credentials
#                     with open(GDRIVE_CREDENTIALS_PATH, "w") as f:
#                         f.write(creds.to_json())
#                 except Exception as e:
#                     print(f"Error refreshing credentials: {e}")
#                 creds = None
#         flow = InstalledAppFlow.from_client_secrets_file(KEYFILE_PATH, DRIVE_SCOPES)
#         creds = flow.run_local_server(port=PORT,    access_type='offline',
#     prompt='consent')
#         pathlib.Path(os.path.dirname(GDRIVE_CREDENTIALS_PATH)).mkdir(parents=True, exist_ok=True)
#         with open(GDRIVE_CREDENTIALS_PATH, "w") as f:
#             f.write(creds.to_json())
#         print(f"Credentials saved to {GDRIVE_CREDENTIALS_PATH}")
#     elif(app == "docs"):
#         if os.path.exists(GDOC_CREDENTIALS_PATH):
#             return
#         creds = None
#         if not creds or not creds.valid:
#             if creds and creds.expired and creds.refresh_token:
#                 try:
#                     creds.refresh(Request())
#                 # Save the refreshed credentials
#                     with open(GDOC_CREDENTIALS_PATH, "w") as f:
#                         f.write(creds.to_json())
#                 except Exception as e:
#                     print(f"Error refreshing credentials: {e}")
#                 creds = None
#         flow = InstalledAppFlow.from_client_secrets_file(KEYFILE_PATH, SCOPES)
#         creds = flow.run_local_server(port=PORT,    access_type='offline', prompt='consent')
#         pathlib.Path(os.path.dirname(GDOC_CREDENTIALS_PATH)).mkdir(parents=True, exist_ok=True)
#         with open(GDOC_CREDENTIALS_PATH, "w") as f:
#             f.write(creds.to_json())
#         print(f"Credentials saved to {GDOC_CREDENTIALS_PATH}")


# =============================================================================
# 2. Session service (per-conversation memory)
# =============================================================================
session_service = InMemorySessionService()


# def list_my_google_docs(tool_context=None, limit: int = 20) -> str:
#     """
#     List the user's most recent Google Docs (this version is ADK-proof).
#     """
#     drive = get_drive_service()
#     results = drive.files().list(
#         q="mimeType='application/vnd.google-apps.document' and trashed=false",
#         orderBy="modifiedTime desc",
#         fields="files(id, name, modifiedTime)",
#         pageSize=limit
#     ).execute()

#     files = results.get('files', [])
#     if not files:
#         return "You have no Google Docs right now."

#     # ADK-safe formatting – one of these two works perfectly:
#     # Option 1 – Markdown code block (best visual result)
#     # doc_list = "Here are your most recent Google Docs:\n\n"
#     # doc_list += "```\n"
#     # for i, f in enumerate(files, 1):
#     #     doc_list += f"{i:2d}. \"{f['name']}\" — {f['modifiedTime'][:10]}\n"
#     # doc_list += "```\n\nJust tell me the title (or number) of the one you want!"

#     # Option 2 – Single-line bullets (also 100 % safe)
#     doc_list = "Your recent docs: " + " | ".join(
#         f"{i}. \"{f['name']}\"" for i, f in enumerate(files[:12], 1)
#     ) + " — Just say the title!"

#     return doc_list

# def find_document_by_title(title: str, tool_context=None) -> str:
#     """
#     Resolve a human title → documentId with caching and disambiguation.
#     """
#     # Fix: Use session.state instead of session directly
#     session_state = (tool_context.session.state if tool_context and tool_context.session else {})
    
#     # Initialize cache if missing
#     if "title_to_id" not in session_state:
#         session_state["title_to_id"] = {}
#     if "last_candidates" not in session_state:
#         session_state["last_candidates"] = []
    
#     clean_title = title.strip().lower()

#     # Cache hit
#     if clean_title in session_state["title_to_id"]:
#         doc_id = session_state["title_to_id"][clean_title]
#         return f"Using cached document '{title}' → ID: {doc_id}"

#     drive = get_drive_service()
#     # Exact match
#     query = f"name = '{title}' and mimeType='application/vnd.google-apps.document' and trashed=false"
#     results = drive.files().list(q=query, fields="files(id,name,modifiedTime)", pageSize=10).execute()
#     files = results.get('files', [])

#     # Fuzzy fallback
#     if not files:
#         fuzzy = f"name contains '{title}' and mimeType='application/vnd.google-apps.document' and trashed=false"
#         files = drive.files().list(q=fuzzy, fields="files(id,name,modifiedTime)", pageSize=20).execute().get('files', [])

#     if not files:
#         return f"Error: No Google Doc found matching title '{title}'"

#     files.sort(key=lambda x: x['modifiedTime'], reverse=True)

#     if len(files) == 1:
#         chosen = files[0]
#         session_state["title_to_id"][clean_title] = chosen['id']
#         # Persist changes back to session
#         if tool_context and tool_context.session:
#             tool_context.session.state = session_state
#         return f"Found document: '{chosen['name']}' → ID: {chosen['id']}"

#     # Multiple → disambiguate
#     session_state["last_candidates"] = files[:10]
#     if tool_context and tool_context.session:
#         tool_context.session.state = session_state
    
#     lines = ["Multiple documents match:"]
#     for i, f in enumerate(files[:8], 1):
#         lines.append(f"{i}. '{f['name']}' (modified {f['modifiedTime'][:10]})")
#     lines.append("\nReply with the number (e.g., 'use 2') or part of the exact title.")
#     return "\n".join(lines)


# def resolve_ambiguity(choice: str, tool_context=None) -> str:
#     """
#     Resolve ambiguity when multiple docs match.
#     """
#     session_state = (tool_context.session.state if tool_context and tool_context.session else {})
#     candidates = session_state.get("last_candidates", [])

#     if not candidates:
#         return "No previous search to clarify."

#     choice_clean = choice.strip().lower()

#     # Numeric choice
#     if choice_clean.isdigit() or (choice_clean.startswith("use ") and choice_clean[4:].strip().isdigit()):
#         idx = int("".join(filter(str.isdigit, choice_clean))) - 1
#         if 0 <= idx < len(candidates):
#             chosen = candidates[idx]
#             session_state.setdefault("title_to_id", {})[chosen['name'].lower()] = chosen['id']
#             session_state["last_candidates"] = []
#             if tool_context and tool_context.session:
#                 tool_context.session.state = session_state
#             return f"Confirmed: using '{chosen['name']}' → ID: {chosen['id']}"

#     # Title substring match
#     for f in candidates:
#         if choice_clean in f['name'].lower() or f['name'].lower() in choice_clean:
#             session_state.setdefault("title_to_id", {})[f['name'].lower()] = f['id']
#             session_state["last_candidates"] = []
#             if tool_context and tool_context.session:
#                 tool_context.session.state = session_state
#             return f"Confirmed: using '{f['name']}' → ID: {f['id']}"

#     return "I couldn't match that choice. Please reply with a number or more of the title."

# def docs_operation(operation: str, document_id: str, content: str = None,
#                    start_index: int = None, end_index: int = None, tool_context=None) -> str:
#     """
#     Read, write, or delete content in a Google Doc.
    
#     Args:
#         operation: 'read', 'write', or 'delete'.
#         document_id: The doc ID.
#         content: Text for write (optional).
#         start_index/end_index: For delete/update (optional).
#         tool_context: ADK-injected context.
    
#     Returns:
#         Result message.
#     """
#     service = get_docs_service()

#     if operation == "read":
#         doc = service.documents().get(documentId=document_id).execute()
#         paragraphs = [elem for elem in doc.get('body', {}).get('content', []) if 'paragraph' in elem]
#         text = ""
#         for p in paragraphs:
#             for elem in p.get('paragraph', {}).get('elements', []):
#                 tr = elem.get('textRun', {})
#                 if tr.get('content'):
#                     text += tr['content']
#         preview = text.replace('\n', ' ')[:1000]
#         return f"Document content preview:\n{preview}" + ("\n..." if len(text) > 1000 else "")

#     elif operation == "write" and content:
#         requests = [{
#             "insertText": {
#                 "location": {"index": start_index or 1},
#                 "text": content + "\n"
#             }
#         }]
#         service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()
#         return f"Successfully added text to document {document_id}"

#     elif operation == "delete" and start_index is not None and end_index is not None:
#         requests = [{
#             "deleteContentRange": {
#                 "range": {"startIndex": start_index, "endIndex": end_index}
#             }
#         }]
#         service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()
#         return f"Deleted content from index {start_index} to {end_index}"

#     else:
#         return "Invalid operation or missing parameters."

# def create_google_doc(title: str, tool_context=None) -> str:
#     """
#     Create a new Google Docs file with the given title.
    
#     Args:
#         title: The title for the new document.
#         tool_context: ADK-injected context.
    
#     Returns:
#         A message with the document ID.
#     """
#     drive = get_drive_service()
#     file_metadata = {
#         'name': title,
#         'mimeType': 'application/vnd.google-apps.document'
#     }
#     file = drive.files().create(body=file_metadata, fields='id').execute()
#     doc_id = file.get('id')
#     return f"Created new Google Doc: '{title}' → ID: {doc_id}"

# def delete_google_doc(document_id: str, tool_context=None) -> str:
#     """
#     Delete a Google Docs file by its document ID.
    
#     Args:
#         document_id: The ID of the document to delete.
#         tool_context: ADK-injected context.
    
#     Returns:
#         Confirmation message upon successful deletion.
#     """
#     drive = get_drive_service()
#     try:
#         drive.files().delete(fileId=document_id).execute()
#         return f"Deleted document with ID: {document_id}"
#     except Exception as e:
#         return f"Failed to delete document: {str(e)}"

# =============================================================================
# Agent (Pass plain functions to tools=)
# =============================================================================
def gdocs_agent():
    return Agent(
        name="gdoc",
        model=Gemini(model="gemini-2.0-flash", retry_options=retry_config),
        instruction="""
        You are an expert Google Docs assistant.

        Core abilities:
        - LIST recent docs: list_my_google_docs
        - FIND docs by title (partial/exact): find_document_by_title (caches results)
        - CREATE new docs: create_google_doc (returns ID)
        - DELETE docs by title OR "the one you just created": find_document_by_title → delete_google_doc
        - READ/WRITE/DELETE content: docs_operation
        - SHARE docs by email: share_google_doc
        - VIEW permissions: get_doc_permissions
        - UPDATE permissions: update_doc_permission

        Smart workflows:
        1. CREATE → "Create 'Meeting Notes'" → caches ID automatically
        2. DELETE → "delete Project Plan" OR "delete the one you created" → find → confirm → delete → list updated
        3. SHARE → "share with john@company.com" → find doc → share as writer
        4. PERMISSIONS → "who has access?" → get_doc_permissions

        Examples users will say:
        - "Create project plan and share with team@company.com"
        - "List my docs" → "delete #2" → "share the new one with client"
        - "Make it public" → share_google_doc(id, None, "reader", type="anyone")
        - "Change john to reader only"

        Rules:
        1. ALWAYS confirm before DELETE (docs OR content): "Are you sure? (y/n)"
        2. Use cached IDs for "the one you just created"
        3. List docs first for vague requests ("what can I delete/share?")
        4. After delete/create/share → show list_my_google_docs
        5. For sharing: default "writer", ask role if unclear ("reader/commenter?")
        6. NEVER delete/share without explicit doc ID or cached match
        """,

        tools=[
            list_my_google_docs,
            find_document_by_title,
            resolve_ambiguity,
            docs_operation,
            create_google_doc,
            delete_google_doc,
            share_google_doc, get_doc_permissions, update_doc_permission
        ],
    )
# ────────────────────────────── RUN ──────────────────────────────
root_agent = gdocs_agent()
runner = Runner(agent=root_agent, app_name="gdoc", session_service=session_service)