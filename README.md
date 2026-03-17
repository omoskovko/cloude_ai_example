# Google Drive MCP Server (Python)

MCP server for reading and searching files on Google Drive via a personal account.

## Project Structure

```
cloude_ai_example/
├── server.py                          # MCP server, entry point
├── drive_client.py                    # Google Drive API client
├── auth.py                            # Standalone script to generate token.json
├── client.py                          # Example client sending requests to the server
├── requirements.txt
├── .env.example                       # Environment variables template
├── credentials.json                   # ← Download from Google Cloud Console
├── token.json                         # ← Generates automatically (don't commit)
├── .env                               # ← Environment variables (copy from .env.example)
```

---

## Setup: Step-by-Step Guide

### Step 1 — Install Dependencies

```bash
cd cloude_ai_example
pip install -r requirements.txt
```

---

### Step 2 — Configure Google Cloud Project

This needs to be done **once** to obtain `credentials.json`.

1. Open [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project → New Project**
3. Name your project (e.g., `mcp-drive`) → **Create**

---

### Step 3 — Enable Google Drive API

1. In the left menu: **APIs & Services → Library**
2. Search for **Google Drive API** → click **Enable**

---

### Step 4 — Create OAuth 2.0 Credentials

1. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
2. If prompted, first configure **OAuth consent screen**:
   - User Type: **External**
   - App name: anything (e.g., `MCP Drive`)
   - Support email: your gmail
   - Click **Save and Continue** on all steps
3. Return to **Create OAuth client ID**:
   - Application type: **Desktop app**
   - Name: `mcp-client`
   - Click **Create**
4. Click **Download JSON** → save as `credentials.json` in the project folder

---

### Step 5 — Add Your Account as Test User

> ⚠️ Required for personal accounts until the application is verified by Google.

1. **APIs & Services → OAuth consent screen → Test users**
2. Click **Add Users** → enter your gmail → **Save**

---

### Step 6 — Generate a Claude API Key

1. Open [Claude Console](https://console.anthropic.com/)
2. Sign in or create an Anthropic account
3. In the left sidebar, go to **API Keys**
4. Click **Create Key**
5. Give the key a name (e.g., `mcp-drive-client`) → click **Create Key**
6. Copy the generated key immediately — it will not be shown again
7. Add the key to your `.env` file:

```
ANTHROPIC_API_KEY=sk-ant-...
```

> ⚠️ Never commit your API key to git. Make sure `.env` is listed in `.gitignore`.

---

### Step 7 — First Authorization

```bash
cp .env.example .env
python server.py
```

On first run, a browser will open automatically.
Sign in to your Google account → click **Allow**.

A `token.json` file will be created — this is your access token.
Future runs won't require the browser.

#### Troubleshooting: browser doesn't open or authorization fails

If the browser doesn't open or you get an authentication error, run `auth.py` directly to generate `token.json`:

```bash
python auth.py
```

A browser window will open — sign in to your Google account and click **Allow**.
Once complete, `token.json` will be created in the project folder.

---

## Usage
1. Start the client:

```bash
python client.py ./server.py
```

## Available Tools

### Search and Navigation
| Tool | Description |
|---|---|
| `search_files` | Search by name or content |
| `list_files` | List files in a folder |
| `list_folders` | List top-level folders |
| `get_folder_contents` | Find folder by name and show contents |
| `get_recent_files` | Recently modified files |

### Reading Files
| Tool | Description |
|---|---|
| `get_file_info` | Metadata: name, type, size, link |
| `read_text_file` | Content of .txt, .md, .csv or Google Doc |
| `read_google_doc` | Google Document content |
| `read_google_sheet` | Google Sheet content in CSV format |

---

## Example Requests to Claude

```
Find files named "test plan" on my Drive

Show the contents of "QA Documents" folder

Read the Google Doc with ID 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms

What files have I edited recently?

Find all CSV files on Drive
```

---

## Security

- **`credentials.json`** and **`token.json`** — never commit to git
- Server has **read-only** permissions (`drive.readonly`)
- Add both files to `.gitignore`:

```
credentials.json
token.json
.env
```

