# Google Drive Sync Utility

A Python utility to synchronize a local folder with a Google Drive folder.

Features:

* Recursive folder traversal
* Automatic folder creation in Google Drive
* Upload new files
* Update existing files only when contents change
* MD5 checksum based synchronization
* Pagination support for large Drive folders
* OAuth2 authentication

---

# Prerequisites

* Python 3.10+
* A Google account
* Access to Google Cloud Console

---

# Project Structure

```text
project/
│
├── integrated_syncr.py
├── credentials.json
├── token.json          # Generated automatically
├── README.md
└── requirements.txt
```

---

# Install Dependencies

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

### Windows

```bash
.venv\Scripts\activate
```

### Linux/macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install google-api-python-client
pip install google-auth-httplib2
pip install google-auth-oauthlib
```

Or create a `requirements.txt`:

```text
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
```

Install:

```bash
pip install -r requirements.txt
```

---

# Google Cloud Setup

## Step 1: Create a Google Cloud Project

1. Open Google Cloud Console.
2. Click **Select Project** → **New Project**.
3. Enter a project name.
4. Click **Create**.

---

## Step 2: Enable Google Drive API

1. Open:

   APIs & Services → Library

2. Search for:

```text
Google Drive API
```

3. Click **Enable**.

---

## Step 3: Configure OAuth Consent Screen

1. Open:

```text
APIs & Services → OAuth consent screen
```

2. Select:

```text
External
```

3. Fill:

* App Name
* User Support Email
* Developer Contact Email

4. Save.

---

## Step 4: Add Test Users

If the application is in testing mode:

1. Open:

```text
OAuth Consent Screen → Audience
```

2. Under **Test Users**, add Google accounts allowed to authenticate.

Example:

```text
your_email@gmail.com
friend@gmail.com
```

Only test users can log in until the app is published.

---

## Step 5: Create OAuth Credentials

Open:

```text
APIs & Services → Credentials
```

Click:

```text
Create Credentials
```

Select:

```text
OAuth Client ID
```

Application type:

```text
Desktop App
```

Enter a name:

```text
Drive Sync
```

Click **Create**.

Download the JSON file.

Rename it to:

```text
credentials.json
```

Place it in the project root.

---

# OAuth Scopes

Current scope:

```python
SCOPES = [
    "https://www.googleapis.com/auth/drive"
]
```

This grants full Google Drive access.

For limited access, consider:

```python
https://www.googleapis.com/auth/drive.file
```

---

# First Execution

Run:

```bash
python integrated_syncr.py
```

The browser opens automatically.

Choose a Google account.

Grant permissions.

After successful authentication:

```text
token.json
```

is generated automatically.

Future executions reuse this token.

---

# Important Files

## credentials.json

Contains OAuth client configuration.

**Do NOT commit to Git.**

---

## token.json

Contains access and refresh tokens.

**Do NOT commit to Git.**

Add to `.gitignore`:

```gitignore
token.json
credentials.json
```

---

# Using the Script

**NOTE:** The name of the local root folder must exactly match the name of the target Google Drive folder for the synchronization to work correctly. Folder names are case-sensitive and must match character-for-character.

✅ **Works:**

* Drive Folder: `Python_Project`
* Local Folder: `Python_Project`

❌ **Does Not Work:**

* Drive Folder: `Pythonproject`
* Local Folder: `Python_project`

If the folder names do not match exactly, the script may fail to correctly map files and folders during synchronization.

Example:

```bash
python integrated_syncr.py \
    "<drive_folder_url>" \
    "<local_folder>"
```

Windows example:

```bash
python integrated_syncr.py ^
    "https://drive.google.com/drive/folders/XXXXXXXX" ^
    "D:\PS\Youtube videos"
```

Example:

```bash
python integrated_syncr.py ^
    "https://drive.google.com/drive/folders/1ABCDEF" ^
    "D:\downloads"
```

---

# Synchronization Behavior

The script:

1. Traverses local files recursively.
2. Traverses Google Drive recursively.
3. Compares file contents using MD5.
4. Uploads missing files.
5. Updates changed files.
6. Creates missing folders automatically.

---

# File Change Detection

Synchronization uses:

```text
MD5 checksum
```

If:

```text
Local MD5 == Drive MD5
```

the file is skipped.

Otherwise:

```text
Drive file is updated.
```

---

# Security Notes

Never share:

```text
credentials.json
token.json
```

Anyone possessing `token.json` may access your Google Drive.

Restrict file permissions when possible.

---

# Troubleshooting

## Invalid Scope Error

Delete:

```text
token.json
```

and authenticate again.

---

## Access Blocked

Ensure your Google account is listed under:

```text
OAuth Consent Screen → Test Users
```

---

## Drive API Disabled

Verify:

```text
Google Drive API
```

is enabled in the Google Cloud project.

---

## Folder Not Found

Ensure the provided Google Drive URL points to a folder and that the authenticated account has access.

---

# Future Improvements

* Bidirectional synchronization
* Delete orphan files
* Resume interrupted uploads
* Parallel uploads
* SHA-256 based verification
* Conflict resolution
* Change history support

---
