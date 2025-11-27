from gdoc.auth import get_drive_service

def share_google_doc(document_id: str, email: str, role: str = "writer", tool_context=None) -> str:
    """
    Share a Google Doc with a specific email address.
    
    Args:
        document_id: The document ID.
        email: Email address to share with.
        role: "reader", "writer", or "commenter" (default: "writer").
    
    Returns:
        Confirmation message.
    """
    drive = get_drive_service()
    try:
        permission = {
            'type': 'user',
            'role': role,
            'emailAddress': email
        }
        drive.permissions().create(fileId=document_id, body=permission, sendNotificationEmail=True).execute()
        return f"Shared '{document_id}' with {email} as {role} ✅"
    except Exception as e:
        return f"Failed to share: {str(e)}"


def get_doc_permissions(document_id: str, tool_context=None) -> str:
    """
    List current sharing permissions for a document.
    """
    drive = get_drive_service()
    try:
        permissions = drive.permissions().list(fileId=document_id).execute()
        perms = permissions.get('permissions', [])
        if not perms:
            return "No sharing permissions set."
        
        lines = [f"Permissions for doc {document_id}:"]
        for p in perms[:10]:  # Limit to 10
            role = p.get('role', 'unknown')
            email = p.get('emailAddress', 'Everyone' if p.get('type') == 'anyone' else 'Group')
            lines.append(f"- {email}: {role}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error getting permissions: {str(e)}"


def update_doc_permission(document_id: str, permission_id: str, role: str, tool_context=None) -> str:
    """
    Update existing permission (e.g., change from writer to reader).
    """
    drive = get_drive_service()
    try:
        drive.permissions().update(fileId=document_id, permissionId=permission_id, body={'role': role}).execute()
        return f"Updated permission {permission_id} to {role}"
    except Exception as e:
        return f"Failed to update permission: {str(e)}"
