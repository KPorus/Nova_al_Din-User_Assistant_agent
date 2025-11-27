from gdoc.auth import get_drive_service
def delete_google_doc(document_id: str, tool_context=None) -> str:
    """
    Delete a Google Docs file by its document ID.
    
    Args:
        document_id: The ID of the document to delete.
        tool_context: ADK-injected context.
    
    Returns:
        Confirmation message upon successful deletion.
    """
    drive = get_drive_service()
    try:
        drive.files().delete(fileId=document_id).execute()
        return f"Deleted document with ID: {document_id}"
    except Exception as e:
        return f"Failed to delete document: {str(e)}"