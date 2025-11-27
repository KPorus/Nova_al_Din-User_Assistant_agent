from gdoc.auth import get_docs_service, get_drive_service

def resolve_ambiguity(choice: str, tool_context=None) -> str:
    """
    Resolve ambiguity when multiple docs match.
    """
    session_state = (tool_context.session.state if tool_context and tool_context.session else {})
    candidates = session_state.get("last_candidates", [])

    if not candidates:
        return "No previous search to clarify."

    choice_clean = choice.strip().lower()

    # Numeric choice
    if choice_clean.isdigit() or (choice_clean.startswith("use ") and choice_clean[4:].strip().isdigit()):
        idx = int("".join(filter(str.isdigit, choice_clean))) - 1
        if 0 <= idx < len(candidates):
            chosen = candidates[idx]
            session_state.setdefault("title_to_id", {})[chosen['name'].lower()] = chosen['id']
            session_state["last_candidates"] = []
            if tool_context and tool_context.session:
                tool_context.session.state = session_state
            return f"Confirmed: using '{chosen['name']}' → ID: {chosen['id']}"

    # Title substring match
    for f in candidates:
        if choice_clean in f['name'].lower() or f['name'].lower() in choice_clean:
            session_state.setdefault("title_to_id", {})[f['name'].lower()] = f['id']
            session_state["last_candidates"] = []
            if tool_context and tool_context.session:
                tool_context.session.state = session_state
            return f"Confirmed: using '{f['name']}' → ID: {f['id']}"

    return "I couldn't match that choice. Please reply with a number or more of the title."

def docs_operation(operation: str, document_id: str, content: str = None,
                   start_index: int = None, end_index: int = None, tool_context=None) -> str:
    """
    Read, write, or delete content in a Google Doc.
    
    Args:
        operation: 'read', 'write', or 'delete'.
        document_id: The doc ID.
        content: Text for write (optional).
        start_index/end_index: For delete/update (optional).
        tool_context: ADK-injected context.
    
    Returns:
        Result message.
    """
    service = get_docs_service()

    if operation == "read":
        doc = service.documents().get(documentId=document_id).execute()
        paragraphs = [elem for elem in doc.get('body', {}).get('content', []) if 'paragraph' in elem]
        text = ""
        for p in paragraphs:
            for elem in p.get('paragraph', {}).get('elements', []):
                tr = elem.get('textRun', {})
                if tr.get('content'):
                    text += tr['content']
        preview = text.replace('\n', ' ')[:1000]
        return f"Document content preview:\n{preview}" + ("\n..." if len(text) > 1000 else "")

    elif operation == "write" and content:
        requests = [{
            "insertText": {
                "location": {"index": start_index or 1},
                "text": content + "\n"
            }
        }]
        service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()
        return f"Successfully added text to document {document_id}"

    elif operation == "delete" and start_index is not None and end_index is not None:
        requests = [{
            "deleteContentRange": {
                "range": {"startIndex": start_index, "endIndex": end_index}
            }
        }]
        service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()
        return f"Deleted content from index {start_index} to {end_index}"

    else:
        return "Invalid operation or missing parameters."

def create_google_doc(title: str, tool_context=None) -> str:
    """
    Create a new Google Docs file with the given title.
    
    Args:
        title: The title for the new document.
        tool_context: ADK-injected context.
    
    Returns:
        A message with the document ID.
    """
    drive = get_drive_service()
    file_metadata = {
        'name': title,
        'mimeType': 'application/vnd.google-apps.document'
    }
    file = drive.files().create(body=file_metadata, fields='id').execute()
    doc_id = file.get('id')
    return f"Created new Google Doc: '{title}' → ID: {doc_id}"