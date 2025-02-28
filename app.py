import os
import sys
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
from tkinter import Tk, filedialog, messagebox, StringVar
import tkinter.ttk as ttk

# Load credentials from environment variable or secure storage
# DO NOT include credentials.json in your code repository
CREDENTIALS_PATH = os.environ.get(
    'GOOGLE_DRIVE_CREDENTIALS', 'credentials.json')
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

try:
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH, scopes=SCOPES)
    drive_service = build("drive", "v3", credentials=creds)
except Exception as e:
    print(f"❌ Authentication error: {e}")
    sys.exit(1)

# Create a simple UI
root = Tk()
root.title("Google Drive Uploader")
root.geometry("500x300")


def select_and_upload():
    # Open folder selection dialog
    folder_path = filedialog.askdirectory(title="Select a Folder to Upload")

    if not folder_path:
        messagebox.showinfo("Info", "No folder selected.")
        return

    # Create a folder in Drive (optional)
    drive_folder_name = folder_name_var.get() or os.path.basename(folder_path)
    folder_metadata = {
        'name': drive_folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }

    try:
        folder = drive_service.files().create(
            body=folder_metadata, fields='id').execute()
        parent_id = folder.get('id')

        # Get all files in the selected folder
        files = [f for f in os.listdir(folder_path) if os.path.isfile(
            os.path.join(folder_path, f))]
        total_files = len(files)

        # Create progress bar
        progress = ttk.Progressbar(
            root, orient="horizontal", length=400, mode="determinate")
        progress.pack(pady=20)
        progress["maximum"] = total_files

        # Show upload status
        status_label = ttk.Label(root, text="Starting upload...")
        status_label.pack(pady=10)

        uploaded_count = 0
        for file_name in files:
            file_path = os.path.join(folder_path, file_name)

            # Update status
            status_label.config(text=f"Uploading: {file_name}")
            root.update_idletasks()

            try:
                # Detect file MIME type (this is more reliable than hardcoding)
                import mimetypes
                file_type = mimetypes.guess_type(
                    file_path)[0] or "application/octet-stream"

                # Upload file to the created folder
                file_metadata = {
                    "name": file_name,
                    "parents": [parent_id]
                }

                media = MediaFileUpload(
                    file_path, mimetype=file_type, resumable=True)
                uploaded_file = drive_service.files().create(
                    body=file_metadata, media_body=media, fields="id").execute()

                uploaded_count += 1
                progress["value"] = uploaded_count
                root.update_idletasks()

            except Exception as e:
                status_label.config(
                    text=f"Error uploading {file_name}: {str(e)}")
                root.update_idletasks()
                continue

        status_label.config(
            text=f"✅ Uploaded {uploaded_count} of {total_files} files to folder: {drive_folder_name}")

    except Exception as e:
        messagebox.showerror("Error", f"Upload failed: {str(e)}")


# UI Components
ttk.Label(root, text="Google Drive Uploader", font=("Arial", 16)).pack(pady=20)

folder_frame = ttk.Frame(root)
folder_frame.pack(pady=10)
ttk.Label(folder_frame, text="Drive Folder Name (optional):").pack(side="left")

folder_name_var = StringVar()  # Fixed: Using tkinter.StringVar directly
ttk.Entry(folder_frame, textvariable=folder_name_var,
          width=30).pack(side="left", padx=5)

ttk.Button(root, text="Select Folder & Upload",
           command=select_and_upload).pack(pady=20)

root.mainloop()
