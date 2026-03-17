"""
Client for working with Google Drive API v3
Documentation: https://developers.google.com/drive/api/v3/reference
"""

import os
import io
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

# Permissions — read-only (most secure option)
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# MIME types for Google formats
GOOGLE_DOC_MIME = "application/vnd.google-apps.document"
GOOGLE_SHEET_MIME = "application/vnd.google-apps.spreadsheet"
GOOGLE_SLIDE_MIME = "application/vnd.google-apps.presentation"
GOOGLE_FOLDER_MIME = "application/vnd.google-apps.folder"


class DriveClient:
    def __init__(self, credentials_file: str, token_file: str):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self._service = None

    def _get_service(self):
        """Get or initialize Google Drive service."""
        if self._service:
            return self._service

        creds = None

        # Load saved token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        # If token is missing or expired — refresh / authorize
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"File '{self.credentials_file}' not found. "
                        "Download credentials.json from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                # Opens browser for authorization
                creds = flow.run_local_server(port=0)

            # Save token for next runs
            with open(self.token_file, "w") as f:
                f.write(creds.to_json())

        self._service = build("drive", "v3", credentials=creds)
        return self._service

    # ------------------------------
    # SEARCH
    # ------------------------------

    def search_files(
        self,
        query: str,
        max_results: int = 20,
        raw_query: bool = False,
        order_by: str = "relevance",
    ) -> dict:
        """Search files. raw_query=True — pass query directly to Drive API."""
        try:
            service = self._get_service()

            # Build Drive Query Language request
            if raw_query:
                drive_query = query
            else:
                # Search by name or fullText
                safe = query.replace("'", "\\'")
                drive_query = (
                    f"(name contains '{safe}' or fullText contains '{safe}') "
                    f"and trashed = false"
                )

            results = (
                service.files()
                .list(
                    q=drive_query,
                    pageSize=max_results,
                    orderBy=order_by,
                    fields="files(id, name, mimeType, size, modifiedTime, webViewLink, parents)",
                )
                .execute()
            )

            files = results.get("files", [])
            return {
                "total": len(files),
                "files": [self._format_file(f) for f in files],
            }

        except HttpError as e:
            return {"error": f"Google API error: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def list_files(self, folder_id: str = "root", max_results: int = 30) -> dict:
        """List files in folder."""
        try:
            service = self._get_service()
            results = (
                service.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed = false",
                    pageSize=max_results,
                    orderBy="folder,name",
                    fields="files(id, name, mimeType, size, modifiedTime, webViewLink)",
                )
                .execute()
            )

            files = results.get("files", [])
            return {
                "total": len(files),
                "files": [self._format_file(f) for f in files],
            }

        except HttpError as e:
            return {"error": f"Google API error: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def list_folders(self) -> dict:
        """List top-level folders."""
        try:
            service = self._get_service()
            results = (
                service.files()
                .list(
                    q=f"mimeType = '{GOOGLE_FOLDER_MIME}' and 'root' in parents and trashed = false",
                    pageSize=50,
                    orderBy="name",
                    fields="files(id, name, modifiedTime)",
                )
                .execute()
            )

            folders = results.get("files", [])
            return {
                "total": len(folders),
                "folders": [
                    {
                        "id": f["id"],
                        "name": f["name"],
                        "modified": f.get("modifiedTime"),
                    }
                    for f in folders
                ],
            }

        except HttpError as e:
            return {"error": f"Google API error: {e}"}
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------
    # READ FILES
    # ------------------------------

    def get_file_info(self, file_id: str) -> dict:
        """Get file metadata."""
        try:
            service = self._get_service()
            file = (
                service.files()
                .get(
                    fileId=file_id,
                    fields="id, name, mimeType, size, createdTime, modifiedTime, webViewLink, description, parents",
                )
                .execute()
            )
            return self._format_file(file)
        except HttpError as e:
            return {"error": f"Google API error: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def read_text_file(self, file_id: str) -> dict:
        """Download and read text file."""
        try:
            service = self._get_service()

            # First check file type
            meta = (
                service.files().get(fileId=file_id, fields="name, mimeType").execute()
            )
            mime = meta.get("mimeType", "")

            # Google formats — need export
            if mime.startswith("application/vnd.google-apps"):
                if mime == GOOGLE_DOC_MIME:
                    return self.export_google_doc(file_id, "text/plain")
                elif mime == GOOGLE_SHEET_MIME:
                    return self.export_google_doc(file_id, "text/csv")
                else:
                    return {
                        "error": f"File type '{mime}' does not support text reading"
                    }

            # Regular files
            request = service.files().get_media(fileId=file_id)
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

            content = buffer.getvalue().decode("utf-8", errors="replace")

            # Limit size (first 10,000 characters)
            truncated = len(content) > 10_000
            return {
                "file_id": file_id,
                "name": meta["name"],
                "content": content[:10_000],
                "truncated": truncated,
                "total_chars": len(content),
            }

        except HttpError as e:
            return {"error": f"Google API error: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def export_google_doc(self, file_id: str, mime_type: str) -> dict:
        """Export Google Doc/Sheet to text format."""
        try:
            service = self._get_service()
            meta = (
                service.files().get(fileId=file_id, fields="name, mimeType").execute()
            )

            content_bytes = (
                service.files().export(fileId=file_id, mimeType=mime_type).execute()
            )

            if isinstance(content_bytes, bytes):
                content = content_bytes.decode("utf-8", errors="replace")
            else:
                content = str(content_bytes)

            truncated = len(content) > 10_000
            return {
                "file_id": file_id,
                "name": meta["name"],
                "exported_as": mime_type,
                "content": content[:10_000],
                "truncated": truncated,
                "total_chars": len(content),
            }

        except HttpError as e:
            return {"error": f"Google API error: {e}"}
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------
    # HELPER METHODS
    # ------------------------------

    def _format_file(self, f: dict) -> dict:
        """Format file for output."""
        mime = f.get("mimeType", "")
        return {
            "id": f["id"],
            "name": f.get("name"),
            "type": self._friendly_type(mime),
            "mime_type": mime,
            "size_bytes": f.get("size"),
            "modified": f.get("modifiedTime"),
            "created": f.get("createdTime"),
            "link": f.get("webViewLink"),
        }

    def _friendly_type(self, mime: str) -> str:
        """Human-readable file type name."""
        mapping = {
            GOOGLE_DOC_MIME: "Google Doc",
            GOOGLE_SHEET_MIME: "Google Sheet",
            GOOGLE_SLIDE_MIME: "Google Slides",
            GOOGLE_FOLDER_MIME: "Folder",
            "application/pdf": "PDF",
            "text/plain": "Text file",
            "text/csv": "CSV",
            "image/jpeg": "Image (JPEG)",
            "image/png": "Image (PNG)",
        }
        return mapping.get(mime, mime)
