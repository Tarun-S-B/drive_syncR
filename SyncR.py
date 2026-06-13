from __future__ import print_function

import os
import os.path
import re
import mimetypes
import hashlib
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# One caveat: Google Docs/Sheets files do not have md5Checksum, but for regular uploaded files like .mp4, .pdf, .zip, etc., this works perfectly.
SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_MIME = "application/vnd.google-apps.folder"

drive_url = sys.argv[1]
local_path = sys.argv[2]

class DriveSyncR:
    def __init__(self, drive_url, local_path):
        self.TOTAL_FILES = 0
        self.UPLOADED_FILES = 0
        self.UNCHANGED_FILES = 0
        self.UPDATED_FILES = 0
        self.FILE_COUNTER = 1
        # LOCAL SETUP 
        self.local_files_dict: dict[str, dict[str, str | int]] = {}

        self.drive_url = drive_url
        self.local_path = local_path

        self.local_root_folder = local_path.split("\\")[-1]

        self.drive_files_dict = {}
        self.drive_folder_dict = {}


    def get_local_md5(self, file_path):
        """create hash of the local file to decide whether to update the file in drive"""
        md5 = hashlib.md5()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5.update(chunk)

        return md5.hexdigest()
 
    def get_drive_service(self):
        """creating the service to interact with Google Drive API"""
        creds = None

        # Load existing token if available
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file(
                "token.json",
                SCOPES
            )

        # If credentials are missing or invalid
        if not creds or not creds.valid:
            # Refresh if expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            # Otherwise login through browser
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json",
                    SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save credntials for future runs
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        return build("drive", "v3", credentials=creds)

    def extract_folder_id(self,url):
        """extract the folder ID from the Drive URL"""
        patterns = [
            r"/folders/([a-zA-Z0-9_-]+)",
            r"id=([a-zA-Z0-9_-]+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError("Could not extract folder ID")

    def walk_drive(self, service, folder_id, path=""):
        """walk throught the drive folder and build the drive_files_dict dictionary"""
        page_token = None

        while True:
            response = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                pageSize=500,
                fields="nextPageToken, files(id,name,mimeType,md5Checksum)",
                pageToken=page_token
            ).execute()

            for item in response.get("files", []):

                current_path = os.path.join(
                    path,
                    item["name"]
                )

                if item["mimeType"] == FOLDER_MIME:
                    self.drive_folder_dict[current_path] = item["id"]

                    self.walk_drive(
                        service,
                        item["id"],
                        current_path
                    )
                else:
                    # drive_files_dict[current_path] = item["id"]
                    self.drive_files_dict[current_path] = {
                        "id": item["id"],
                        "md5": item.get("md5Checksum")
                    }

            page_token = response.get("nextPageToken")

            if page_token is None:
                break

    def upload_file(self, service, local_file, parent_id):
        """upload the local file which doesn't exist in the drive"""
        mime_type, _ = mimetypes.guess_type(local_file)
        media = MediaFileUpload(
            local_file,
            mimetype=mime_type,
            resumable=True
        )

        metadata = {
            "name": os.path.basename(local_file),
            "parents": [parent_id]
        }

        service.files().create(
            body=metadata,
            media_body=media
        ).execute()

    def update_file(self, service, file_id, local_file):
        """update the outdated drive file with the updated local file based on the md5 hash of that file"""
        mime_type, _ = mimetypes.guess_type(local_file)
        media = MediaFileUpload(
            local_file,
            mimetype=mime_type,
            resumable=True
        )

        service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()

    def sync_file(self,service,relative_path, local_info):
        """Depending on the state either upload the local file, update the local to drive or keep it unchanged"""
        if relative_path in self.drive_files_dict:

            drive_info = self.drive_files_dict[relative_path]

            local_md5 = self.get_local_md5(local_info["path"])

            if local_md5 != drive_info["md5"]:
                print(f"{self.FILE_COUNTER}) Updating: {relative_path} \tSize: {local_info['size']}")
                self.UPDATED_FILES += 1
                self.FILE_COUNTER += 1

                self.update_file( service, drive_info["id"], local_info["path"])
            else:
                print(f"{self.FILE_COUNTER}) Unchanged: {relative_path} \tSize: {local_info['size']}")
                self.UNCHANGED_FILES += 1
                self.FILE_COUNTER += 1
        else:
            print(f"{self.FILE_COUNTER}) Uploading: {relative_path} \tSize: {local_info['size']}")
            parent_path = os.path.dirname(relative_path)
            parent_id = self.ensure_drive_folder( service, parent_path )
            self.upload_file( service, local_info["path"], parent_id )
            self.UPLOADED_FILES += 1
            self.FILE_COUNTER += 1

    def create_drive_folder(self, service, folder_name, parent_id ):
        """create the folder in drive if it exists in local directory but not in drive"""
        metadata = {
            "name": folder_name,
            "mimeType": FOLDER_MIME,
            "parents": [parent_id]
        }

        folder = service.files().create(
            body=metadata,
            fields="id,name"
        ).execute()

        print(
            f"Created folder: "
            f"{folder['name']} "
            f"({folder['id']})"
        )

        return folder["id"]

    def ensure_drive_folder(self, service, folder_path ):
        """returns the folder id for the folder in drive"""
        if folder_path in self.drive_folder_dict:
            return self.drive_folder_dict[folder_path]

        parent_path = os.path.dirname(folder_path)
        folder_name = os.path.basename(folder_path)

        parent_id = self.ensure_drive_folder(
            service,
            parent_path
        )

        folder_id = self.create_drive_folder( service, folder_name, parent_id )

        self.drive_folder_dict[folder_path] = folder_id

        return folder_id

if __name__ == "__main__":   
    syncr = DriveSyncR(drive_url=sys.argv[1], local_path = sys.argv[2])

    for dirpath, dirnames, filenames in os.walk(syncr.local_path, followlinks=False):
        for filename in filenames:
            relative = os.path.relpath(
                os.path.join(dirpath, filename),
                os.path.dirname(local_path)
            )

            file_path = os.path.join(
                dirpath,
                filename
            )

            syncr.local_files_dict[relative] = {
                "path": os.path.join( dirpath, filename ),
                "size": f"{os.path.getsize(file_path)/(1024*1024):.2f} MB" 
            } 

    TOTAL_FILES = len(syncr.local_files_dict)
    # DRIVE SETUP
    # Create Drive service
    print("-----------------------------------------------------------------")
    print(f"TOTAL FILES: {TOTAL_FILES}")
    print("-----------------------------------------------------------------")

    service = syncr.get_drive_service()



    folder_id = syncr.extract_folder_id(drive_url)

    folder = service.files().get(
        fileId=folder_id,
        fields="id,name"
    ).execute()

    drive_root = folder["name"]
    syncr.drive_folder_dict[drive_root] = folder_id

    if syncr.local_root_folder != drive_root:
        raise ValueError(
            "Local root folder and Drive root folder names must match"
        )

    syncr.walk_drive(
        service,
        folder_id,
        drive_root
    )

    for relative_path, local_info in syncr.local_files_dict.items():
        syncr.sync_file( service, relative_path, local_info )

    # global TOTAL_FILES, UNCHANGED_FILES, UPDATED_FILES, UPLOADED_FILES
    print("\n\n")
    print(f"TOTAL FILES:\t{syncr.TOTAL_FILES}")
    print(f"UNCHANGED:\t{syncr.UNCHANGED_FILES}")
    print(f"UPDATED:\t{syncr.UPDATED_FILES}")
    print(f"UPLOADED:\t{syncr.UPLOADED_FILES}")
