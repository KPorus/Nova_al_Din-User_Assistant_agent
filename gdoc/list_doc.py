from gdoc.auth import get_drive_service

def list_my_google_docs(tool_context=None, limit: int = 20) -> str:
    """
    List the user's most recent Google Docs (this version is ADK-proof).
    """
    drive = get_drive_service()
    results = drive.files().list(
        q="mimeType='application/vnd.google-apps.document' and trashed=false",
        orderBy="modifiedTime desc",
        fields="files(id, name, modifiedTime)",
        pageSize=limit
    ).execute()

    files = results.get('files', [])
    if not files:
        return "You have no Google Docs right now."

    doc_list = "Your recent docs: " + " | ".join(
        f"{i}. \"{f['name']}\"" for i, f in enumerate(files[:12], 1)
    ) + " — Just say the title!"

    return doc_list

def find_document_by_title(title: str, tool_context=None) -> str:
    """
    Resolve a human title → documentId with caching and disambiguation.
    """
    # Fix: Use session.state instead of session directly
    session_state = (tool_context.session.state if tool_context and tool_context.session else {})
    
    # Initialize cache if missing
    if "title_to_id" not in session_state:
        session_state["title_to_id"] = {}
    if "last_candidates" not in session_state:
        session_state["last_candidates"] = []
    
    clean_title = title.strip().lower()

    # Cache hit
    if clean_title in session_state["title_to_id"]:
        doc_id = session_state["title_to_id"][clean_title]
        return f"Using cached document '{title}' → ID: {doc_id}"

    drive = get_drive_service()
    # Exact match
    query = f"name = '{title}' and mimeType='application/vnd.google-apps.document' and trashed=false"
    results = drive.files().list(q=query, fields="files(id,name,modifiedTime)", pageSize=10).execute()
    files = results.get('files', [])

    # Fuzzy fallback
    if not files:
        fuzzy = f"name contains '{title}' and mimeType='application/vnd.google-apps.document' and trashed=false"
        files = drive.files().list(q=fuzzy, fields="files(id,name,modifiedTime)", pageSize=20).execute().get('files', [])

    if not files:
        return f"Error: No Google Doc found matching title '{title}'"

    files.sort(key=lambda x: x['modifiedTime'], reverse=True)

    if len(files) == 1:
        chosen = files[0]
        session_state["title_to_id"][clean_title] = chosen['id']
        # Persist changes back to session
        if tool_context and tool_context.session:
            tool_context.session.state = session_state
        return f"Found document: '{chosen['name']}' → ID: {chosen['id']}"

    # Multiple → disambiguate
    session_state["last_candidates"] = files[:10]
    if tool_context and tool_context.session:
        tool_context.session.state = session_state
    
    lines = ["Multiple documents match:"]
    for i, f in enumerate(files[:8], 1):
        lines.append(f"{i}. '{f['name']}' (modified {f['modifiedTime'][:10]})")
    lines.append("\nReply with the number (e.g., 'use 2') or part of the exact title.")
    return "\n".join(lines)

