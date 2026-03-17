"""
Google Drive MCP Server — read and search files
Uses OAuth 2.0 for personal Google account
"""

import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from drive_client import DriveClient

load_dotenv()

# --- Initialization ---
mcp = FastMCP("gdrive-server")
drive = DriveClient(
    credentials_file=os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json"),
    token_file=os.getenv("GOOGLE_TOKEN_FILE", "token.json"),
)


# -----------------------------------------
# TOOLS: SEARCH
# -----------------------------------------


@mcp.tool()
def search_files(query: str, max_results: int = 20) -> dict:
    """
    Search files on Google Drive by name or content.

    Args:
        query: Search query, e.g., 'april report' or 'test plan'
        max_results: Maximum number of results (default 20)
    """
    return drive.search_files(query, max_results)


@mcp.tool()
def list_files(folder_id: str = "root", max_results: int = 30) -> dict:
    """
    Get a list of files in a folder.

    Args:
        folder_id: Folder ID (default 'root' — drive root)
        max_results: Maximum number of files
    """
    return drive.list_files(folder_id, max_results)


@mcp.tool()
def list_folders() -> dict:
    """Get a list of all folders on Google Drive (top level)."""
    return drive.list_folders()


# -----------------------------------------
# TOOLS: READ FILES
# -----------------------------------------


@mcp.tool()
def get_file_info(file_id: str) -> dict:
    """
    Get file metadata: name, type, size, modified date, link.

    Args:
        file_id: File ID from Google Drive
    """
    return drive.get_file_info(file_id)


@mcp.tool()
def read_text_file(file_id: str) -> dict:
    """
    Read the content of a text file (.txt, .md, .csv, Google Docs).

    Args:
        file_id: File ID from Google Drive
    """
    return drive.read_text_file(file_id)


@mcp.tool()
def read_google_doc(file_id: str) -> dict:
    """
    Read the content of a Google Document (Google Docs).

    Args:
        file_id: Google Doc file ID
    """
    return drive.export_google_doc(file_id, mime_type="text/plain")


@mcp.tool()
def read_google_sheet(file_id: str) -> dict:
    """
    Read the content of a Google Sheet (Google Sheets) in CSV format.

    Args:
        file_id: Google Sheets file ID
    """
    return drive.export_google_doc(file_id, mime_type="text/csv")


# -----------------------------------------
# TOOLS: NAVIGATION
# -----------------------------------------


@mcp.tool()
def get_folder_contents(folder_name: str) -> dict:
    """
    Find a folder by name and show its contents.

    Args:
        folder_name: Folder name, e.g., 'Projects' or 'QA Documents'
    """
    # First find the folder by name
    result = drive.search_files(
        query=f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'",
        max_results=5,
        raw_query=True,
    )
    folders = result.get("files", [])
    if not folders:
        return {"error": f"Folder '{folder_name}' not found"}

    folder_id = folders[0]["id"]
    contents = drive.list_files(folder_id, max_results=50)
    contents["folder"] = folders[0]["name"]
    contents["folder_id"] = folder_id
    return contents


@mcp.tool()
def get_recent_files(max_results: int = 20) -> dict:
    """
    Get a list of recently modified files on Google Drive.

    Args:
        max_results: Number of files (default 20)
    """
    return drive.search_files(
        query="modifiedTime > '2024-01-01T00:00:00'",
        max_results=max_results,
        raw_query=True,
        order_by="modifiedTime desc",
    )


if __name__ == "__main__":
    mcp.run()
