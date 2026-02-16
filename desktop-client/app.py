import json
import hashlib
import mimetypes
import os
import re
import threading
import uuid
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from tkinter import END, BOTH, LEFT, RIGHT, X, filedialog, messagebox, ttk
import tkinter as tk

from google.auth.transport.requests import Request as GoogleAuthRequest
from google_auth_oauthlib.flow import InstalledAppFlow
import requests

try:
    from PIL import ExifTags, Image
except Exception:
    ExifTags = None
    Image = None


DEFAULT_API_BASE_URL = "https://09ew2nqn27.execute-api.us-east-1.amazonaws.com"
DEFAULT_OAUTH_CLIENT_FILE = os.path.join(os.path.dirname(__file__), "google_oauth_client.json")
GOOGLE_OAUTH_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

SUPPORTED_MEDIA_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".mp4", ".mov", ".mkv"
}
SYNC_IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic"
}
SYNC_VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".mkv"
}
MAX_QUEUE_PARALLELISM = 4
DEFAULT_QUEUE_PARALLELISM = 2
DEFAULT_DESKTOP_STATE_FILE = os.path.join(os.path.dirname(__file__), "desktop_state.json")


def pretty_json(value):
    return json.dumps(value, indent=2, ensure_ascii=False)


class MillerPicDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MillerPic Desktop Client")
        self.root.geometry("860x640")

        self.api_base_url_var = tk.StringVar(value=DEFAULT_API_BASE_URL)
        self.id_token_var = tk.StringVar()
        self.auth_status_var = tk.StringVar(value="Not signed in")
        self.selected_file_var = tk.StringVar()
        self.selected_file_name_var = tk.StringVar()
        self.selected_folder_var = tk.StringVar()
        self.content_type_var = tk.StringVar(value="image/webp")
        self.photo_id_var = tk.StringVar()
        self.download_photo_id_var = tk.StringVar()
        self.list_limit_var = tk.StringVar(value="20")
        self.list_next_token_var = tk.StringVar()
        self.search_query_var = tk.StringVar()
        self.search_limit_var = tk.StringVar(value="20")
        self.queue_parallelism_var = tk.StringVar(value=str(DEFAULT_QUEUE_PARALLELISM))
        self.queue_status_filter_var = tk.StringVar(value="ALL")
        self.queue_search_filter_var = tk.StringVar()
        self.latest_photos = []
        self.upload_queue_items = []
        self.upload_queue_running = False
        self.upload_queue_lock = threading.Lock()
        self.managed_folders = []
        self.synced_files = {}
        self._queue_refresh_scheduled = False
        self.google_credentials = None

        self._load_local_state()

        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill=BOTH, expand=True)

        auth_frame = ttk.LabelFrame(container, text="Connection + Auth", padding=10)
        auth_frame.pack(fill=X)

        ttk.Label(auth_frame, text="API Base URL").grid(row=0, column=0, sticky="w")
        ttk.Entry(auth_frame, textvariable=self.api_base_url_var, width=95).grid(
            row=1, column=0, sticky="ew", pady=(0, 8)
        )

        ttk.Label(auth_frame, text="Google ID Token (Bearer)").grid(row=2, column=0, sticky="w")
        ttk.Entry(auth_frame, textvariable=self.id_token_var, width=95, show="*").grid(
            row=3, column=0, sticky="ew"
        )

        auth_actions = ttk.Frame(auth_frame)
        auth_actions.grid(row=4, column=0, sticky="w", pady=(8, 0))
        ttk.Button(auth_actions, text="Sign in with Google", command=self.on_google_sign_in).pack(side=LEFT)
        ttk.Button(auth_actions, text="Sign out", command=self.on_google_sign_out).pack(side=LEFT, padx=(8, 0))
        ttk.Label(auth_actions, textvariable=self.auth_status_var).pack(side=LEFT, padx=(12, 0))

        upload_frame = ttk.LabelFrame(container, text="Upload Photo", padding=10)
        upload_frame.pack(fill=X, pady=(12, 0))

        file_row = ttk.Frame(upload_frame)
        file_row.pack(fill=X)
        ttk.Entry(file_row, textvariable=self.selected_file_var).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(file_row, text="Browse", command=self.on_select_file).pack(side=RIGHT, padx=(8, 0))

        input_row = ttk.Frame(upload_frame)
        input_row.pack(fill=X, pady=(8, 0))

        ttk.Label(input_row, text="Photo ID").grid(row=0, column=0, sticky="w")
        ttk.Entry(input_row, textvariable=self.photo_id_var, width=40).grid(row=1, column=0, padx=(0, 12), sticky="w")

        ttk.Label(input_row, text="Content-Type").grid(row=0, column=1, sticky="w")
        ttk.Entry(input_row, textvariable=self.content_type_var, width=35).grid(row=1, column=1, sticky="w")

        ttk.Button(upload_frame, text="Upload Selected File", command=self.on_upload).pack(anchor="w", pady=(10, 0))

        folder_row = ttk.Frame(upload_frame)
        folder_row.pack(fill=X, pady=(10, 0))
        ttk.Entry(folder_row, textvariable=self.selected_folder_var).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(folder_row, text="Browse Folder", command=self.on_select_folder).pack(side=RIGHT, padx=(8, 0))

        managed_actions_row = ttk.Frame(upload_frame)
        managed_actions_row.pack(fill=X, pady=(8, 0))
        ttk.Button(managed_actions_row, text="Add Managed Folder", command=self.on_add_managed_folder).pack(side=LEFT)
        ttk.Button(managed_actions_row, text="Remove Managed Folder", command=self.on_remove_managed_folder).pack(side=LEFT, padx=(8, 0))
        ttk.Button(managed_actions_row, text="Run Sync Job", command=self.on_run_sync_job).pack(side=LEFT, padx=(8, 0))

        self.managed_folders_tree = ttk.Treeview(
            upload_frame,
            columns=("path",),
            show="headings",
            height=3,
        )
        self.managed_folders_tree.heading("path", text="Managed Folders")
        self.managed_folders_tree.column("path", width=820)
        self.managed_folders_tree.pack(fill=X, pady=(8, 0))
        self._refresh_managed_folders_tree()

        queue_actions_row = ttk.Frame(upload_frame)
        queue_actions_row.pack(fill=X, pady=(8, 0))
        ttk.Button(queue_actions_row, text="Enqueue Folder Files", command=self.on_enqueue_folder).pack(side=LEFT)
        ttk.Button(queue_actions_row, text="Run Upload Queue", command=self.on_run_upload_queue).pack(side=LEFT, padx=(8, 0))
        ttk.Button(queue_actions_row, text="Retry Failed", command=self.on_retry_failed_queue_items).pack(side=LEFT, padx=(8, 0))
        ttk.Button(queue_actions_row, text="Cancel Queued", command=self.on_cancel_queued_items).pack(side=LEFT, padx=(8, 0))

        queue_config_row = ttk.Frame(upload_frame)
        queue_config_row.pack(fill=X, pady=(8, 0))
        ttk.Label(queue_config_row, text=f"Parallel uploads (1-{MAX_QUEUE_PARALLELISM})").pack(side=LEFT)
        ttk.Entry(queue_config_row, textvariable=self.queue_parallelism_var, width=6).pack(side=LEFT, padx=(8, 0))

        self.queue_tree = ttk.Treeview(
            upload_frame,
            columns=("file", "status", "message"),
            show="headings",
            height=5,
        )
        self.queue_tree.heading("file", text="File")
        self.queue_tree.heading("status", text="Status")
        self.queue_tree.heading("message", text="Message")
        self.queue_tree.column("file", width=260)
        self.queue_tree.column("status", width=120)
        self.queue_tree.column("message", width=420)
        self.queue_tree.pack(fill=X, pady=(8, 0))

        queue_manage_row = ttk.Frame(upload_frame)
        queue_manage_row.pack(fill=X, pady=(8, 0))
        ttk.Label(queue_manage_row, text="Queue Filter").pack(side=LEFT)
        queue_status_values = [
            "ALL", "QUEUED", "UPLOADING", "COMPLETED", "FAILED", "SKIPPED_VIDEO", "CANCELLED"
        ]
        ttk.Combobox(
            queue_manage_row,
            textvariable=self.queue_status_filter_var,
            values=queue_status_values,
            width=14,
            state="readonly",
        ).pack(side=LEFT, padx=(8, 0))
        ttk.Entry(queue_manage_row, textvariable=self.queue_search_filter_var, width=24).pack(side=LEFT, padx=(8, 0))
        ttk.Button(queue_manage_row, text="Apply", command=self.on_apply_queue_filters).pack(side=LEFT, padx=(8, 0))
        ttk.Button(queue_manage_row, text="Reset", command=self.on_reset_queue_filters).pack(side=LEFT, padx=(8, 0))
        ttk.Button(queue_manage_row, text="Clear Completed", command=self.on_clear_completed_queue_items).pack(side=LEFT, padx=(12, 0))
        ttk.Button(queue_manage_row, text="Clear Failed", command=self.on_clear_failed_queue_items).pack(side=LEFT, padx=(8, 0))
        ttk.Button(queue_manage_row, text="Clear Skipped", command=self.on_clear_skipped_queue_items).pack(side=LEFT, padx=(8, 0))

        download_frame = ttk.LabelFrame(container, text="Get Download URL", padding=10)
        download_frame.pack(fill=X, pady=(12, 0))

        ttk.Label(download_frame, text="Photo ID").grid(row=0, column=0, sticky="w")
        ttk.Entry(download_frame, textvariable=self.download_photo_id_var, width=40).grid(
            row=1, column=0, sticky="w", padx=(0, 10)
        )
        ttk.Button(download_frame, text="Fetch Download URL", command=self.on_get_download_url).grid(
            row=1, column=1, sticky="w"
        )

        search_frame = ttk.LabelFrame(container, text="Search Photos", padding=10)
        search_frame.pack(fill=X, pady=(12, 0))

        ttk.Label(search_frame, text="Search Query (filename/subjects)").grid(row=0, column=0, sticky="w")
        ttk.Entry(search_frame, textvariable=self.search_query_var, width=60).grid(
            row=1, column=0, sticky="ew", padx=(0, 10)
        )

        ttk.Label(search_frame, text="Limit").grid(row=0, column=1, sticky="w")
        ttk.Entry(search_frame, textvariable=self.search_limit_var, width=8).grid(
            row=1, column=1, sticky="w", padx=(0, 10)
        )

        ttk.Button(search_frame, text="Search", command=self.on_search_photos).grid(row=1, column=2, sticky="w")

        search_frame.columnconfigure(0, weight=1)

        list_frame = ttk.LabelFrame(container, text="List Photos", padding=10)
        list_frame.pack(fill=X, pady=(12, 0))

        ttk.Label(list_frame, text="Limit").grid(row=0, column=0, sticky="w")
        ttk.Entry(list_frame, textvariable=self.list_limit_var, width=8).grid(row=1, column=0, sticky="w", padx=(0, 10))

        ttk.Label(list_frame, text="Next Token (optional)").grid(row=0, column=1, sticky="w")
        ttk.Entry(list_frame, textvariable=self.list_next_token_var, width=72).grid(row=1, column=1, sticky="ew", padx=(0, 10))

        ttk.Button(list_frame, text="List Photos", command=self.on_list_photos).grid(row=1, column=2, sticky="w")

        self.photos_tree = ttk.Treeview(
            list_frame,
            columns=("fileName", "photoId", "contentType", "createdAt"),
            show="headings",
            height=6,
        )
        self.photos_tree.heading("fileName", text="File Name")
        self.photos_tree.heading("photoId", text="Photo ID")
        self.photos_tree.heading("contentType", text="Content-Type")
        self.photos_tree.heading("createdAt", text="Created At")
        self.photos_tree.column("fileName", width=260)
        self.photos_tree.column("photoId", width=240)
        self.photos_tree.column("contentType", width=150)
        self.photos_tree.column("createdAt", width=180)
        self.photos_tree.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 0))

        actions_row = ttk.Frame(list_frame)
        actions_row.grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Button(actions_row, text="Use Selected for Download", command=self.on_use_selected_photo).pack(side=LEFT)
        ttk.Button(actions_row, text="Open Selected Image", command=self.on_open_selected_image).pack(side=LEFT, padx=(8, 0))

        list_frame.columnconfigure(1, weight=1)

        output_frame = ttk.LabelFrame(container, text="Output", padding=10)
        output_frame.pack(fill=BOTH, expand=True, pady=(12, 0))

        self.output_text = tk.Text(output_frame, wrap="word")
        self.output_text.pack(fill=BOTH, expand=True)

        self.log("Desktop client ready.")

    def log(self, message):
        self.output_text.insert(END, message + "\n")
        self.output_text.see(END)

    def set_photo_id_if_empty(self, value):
        if not self.photo_id_var.get().strip():
            self.photo_id_var.set(value)

    def _oauth_client_file(self):
        return os.environ.get("MILLERPIC_GOOGLE_OAUTH_CLIENT_FILE") or DEFAULT_OAUTH_CLIENT_FILE

    def on_google_sign_in(self):
        self._run_in_thread(self._google_sign_in_flow)

    def _google_sign_in_flow(self):
        client_file = self._oauth_client_file()
        if not os.path.isfile(client_file):
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Missing OAuth config",
                    f"Could not find Google OAuth client file:\n{client_file}\n\n"
                    "Create a Desktop OAuth client in Google Cloud and save the JSON to this path, "
                    "or set MILLERPIC_GOOGLE_OAUTH_CLIENT_FILE.",
                ),
            )
            return

        try:
            self.log("Starting Google sign-in flow in browser...")
            flow = InstalledAppFlow.from_client_secrets_file(client_file, scopes=GOOGLE_OAUTH_SCOPES)
            credentials = flow.run_local_server(
                host="localhost",
                port=0,
                open_browser=True,
                authorization_prompt_message="A browser window has been opened for Google sign-in.",
                success_message="MillerPic authentication complete. You can close this tab.",
            )

            if not credentials.id_token and credentials.refresh_token:
                credentials.refresh(GoogleAuthRequest())

            if not credentials.id_token:
                raise RuntimeError("Google sign-in succeeded but no ID token was returned.")

            self.root.after(0, self._apply_google_credentials, credentials)
        except Exception as error:
            self.log(f"Google sign-in failed: {error}")
            self.root.after(0, lambda: messagebox.showerror("Google sign-in failed", str(error)))

    def _apply_google_credentials(self, credentials):
        self.google_credentials = credentials
        self.id_token_var.set(credentials.id_token or "")

        expiry = credentials.expiry
        if isinstance(expiry, datetime):
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            expiry_text = expiry.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        else:
            expiry_text = "unknown"

        self.auth_status_var.set(f"Signed in (expires: {expiry_text})")
        self.log("Google sign-in complete. Token field updated.")

    def on_google_sign_out(self):
        self.google_credentials = None
        self.id_token_var.set("")
        self.auth_status_var.set("Not signed in")
        self.log("Signed out locally (token cleared).")

    def _refresh_google_token_if_needed(self):
        credentials = self.google_credentials
        if not credentials:
            return

        if not credentials.expired:
            if credentials.id_token:
                self.id_token_var.set(credentials.id_token)
            return

        if not credentials.refresh_token:
            self.log("Google token expired and no refresh token is available. Please sign in again.")
            return

        try:
            credentials.refresh(GoogleAuthRequest())
            if credentials.id_token:
                self.id_token_var.set(credentials.id_token)
            self._apply_google_credentials(credentials)
            self.log("Refreshed Google token automatically.")
        except Exception as error:
            self.log(f"Automatic token refresh failed: {error}")

    def on_select_file(self):
        file_path = filedialog.askopenfilename(
            title="Select photo or video",
            filetypes=[
                ("Media", "*.jpg *.jpeg *.png *.webp *.gif *.heic *.mp4 *.mov *.mkv"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        self.selected_file_var.set(file_path)
        self.selected_file_name_var.set(os.path.basename(file_path))
        guessed_type, _ = mimetypes.guess_type(file_path)
        if guessed_type:
            self.content_type_var.set(guessed_type)

        generated_photo_id = uuid.uuid4().hex
        self.set_photo_id_if_empty(generated_photo_id)
        self.log(f"Selected file: {file_path}")
        self.log(f"Auto-filled photo ID: {self.photo_id_var.get()}")

    def on_select_folder(self):
        folder_path = filedialog.askdirectory(title="Select folder with photos/videos")
        if not folder_path:
            return
        self.selected_folder_var.set(folder_path)
        self.log(f"Selected folder: {folder_path}")

    def _desktop_state_file_path(self):
        return os.environ.get("MILLERPIC_DESKTOP_STATE_FILE") or DEFAULT_DESKTOP_STATE_FILE

    @staticmethod
    def _normalize_path(path_value):
        return os.path.normcase(os.path.normpath(os.path.abspath(path_value)))

    @staticmethod
    def _build_file_signature(file_path):
        try:
            stats = os.stat(file_path)
            return f"{stats.st_size}:{stats.st_mtime_ns}"
        except OSError:
            return None

    @staticmethod
    def _compute_content_hash(file_path):
        digest = hashlib.sha256()
        try:
            with open(file_path, "rb") as source:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
            return digest.hexdigest()
        except OSError:
            return None

    @staticmethod
    def _is_sync_image_file(file_name):
        extension = os.path.splitext(file_name)[1].lower()
        return extension in SYNC_IMAGE_EXTENSIONS

    @staticmethod
    def _is_sync_video_file(file_name):
        extension = os.path.splitext(file_name)[1].lower()
        return extension in SYNC_VIDEO_EXTENSIONS

    @staticmethod
    def _normalize_subject_label(value):
        normalized = str(value or "").strip().lower()
        return normalized

    @staticmethod
    def _dedupe_subjects(subjects):
        seen = set()
        deduped = []
        for subject in subjects:
            normalized = MillerPicDesktopApp._normalize_subject_label(subject)
            if not normalized:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(normalized)
        return deduped

    @staticmethod
    def _to_float(value):
        try:
            return float(value)
        except Exception:
            return None

    @staticmethod
    def _gps_to_decimal(values, reference):
        if not values or len(values) != 3:
            return None

        degrees = MillerPicDesktopApp._to_float(values[0])
        minutes = MillerPicDesktopApp._to_float(values[1])
        seconds = MillerPicDesktopApp._to_float(values[2])
        if degrees is None or minutes is None or seconds is None:
            return None

        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        ref = str(reference or "").upper()
        if ref in {"S", "W"}:
            decimal = -decimal
        return decimal

    def _extract_exif_subjects(self, file_path):
        if Image is None or ExifTags is None:
            return []

        try:
            with Image.open(file_path) as image:
                exif_data = image.getexif()
                if not exif_data:
                    return []

                tag_map = {
                    ExifTags.TAGS.get(tag_id, tag_id): value
                    for tag_id, value in exif_data.items()
                }

                subjects = []
                date_taken = tag_map.get("DateTimeOriginal") or tag_map.get("DateTime")
                if isinstance(date_taken, str):
                    try:
                        parsed = datetime.strptime(date_taken, "%Y:%m:%d %H:%M:%S")
                        subjects.append(f"date:{parsed.date().isoformat()}")
                    except ValueError:
                        pass

                gps_raw = tag_map.get("GPSInfo")
                if isinstance(gps_raw, dict):
                    gps_map = {
                        ExifTags.GPSTAGS.get(gps_tag, gps_tag): gps_value
                        for gps_tag, gps_value in gps_raw.items()
                    }
                    latitude = self._gps_to_decimal(gps_map.get("GPSLatitude"), gps_map.get("GPSLatitudeRef"))
                    longitude = self._gps_to_decimal(gps_map.get("GPSLongitude"), gps_map.get("GPSLongitudeRef"))
                    if latitude is not None and longitude is not None:
                        subjects.append(f"geo:{latitude:.5f},{longitude:.5f}")

                return subjects
        except Exception:
            return []

    def _extract_folder_subjects(self, file_path, managed_root=None):
        if not managed_root:
            return []

        folder_subjects = []
        normalized_root = self._normalize_path(managed_root)
        normalized_file = self._normalize_path(file_path)
        try:
            common_path = os.path.commonpath([normalized_root, normalized_file])
        except ValueError:
            return folder_subjects
        if common_path != normalized_root:
            return folder_subjects

        root_label = os.path.basename(normalized_root)
        if root_label:
            folder_subjects.append(f"folder:{root_label}")

        parent_dir = os.path.dirname(normalized_file)
        relative_dir = os.path.relpath(parent_dir, normalized_root)
        if relative_dir not in {".", ""}:
            for segment in relative_dir.split(os.sep):
                if segment and segment != ".":
                    folder_subjects.append(f"folder:{segment}")

        return folder_subjects

    def _build_subjects_for_file(self, file_path, managed_root=None):
        subjects = []
        subjects.extend(self._extract_folder_subjects(file_path, managed_root))
        subjects.extend(self._extract_exif_subjects(file_path))
        return self._dedupe_subjects(subjects)

    def _load_local_state(self):
        state_path = self._desktop_state_file_path()
        if not os.path.isfile(state_path):
            return

        try:
            with open(state_path, "r", encoding="utf-8") as state_file:
                data = json.load(state_file)
        except Exception as error:
            print(f"Could not load desktop state: {error}")
            return

        folders = data.get("managedFolders") or []
        managed = []
        for folder in folders:
            if not isinstance(folder, str):
                continue
            if not os.path.isdir(folder):
                continue
            managed.append(self._normalize_path(folder))

        synced_files = data.get("syncedFiles")
        if not isinstance(synced_files, dict):
            synced_files = {}

        self.managed_folders = sorted(set(managed))
        self.synced_files = synced_files

    def _save_local_state(self):
        payload = {
            "managedFolders": self.managed_folders,
            "syncedFiles": self.synced_files,
        }
        state_path = self._desktop_state_file_path()
        try:
            with open(state_path, "w", encoding="utf-8") as state_file:
                json.dump(payload, state_file, indent=2, ensure_ascii=False)
        except Exception as error:
            self.log(f"Could not save desktop state: {error}")

    def _refresh_managed_folders_tree(self):
        for row_id in self.managed_folders_tree.get_children():
            self.managed_folders_tree.delete(row_id)

        for index, folder_path in enumerate(self.managed_folders):
            self.managed_folders_tree.insert("", "end", iid=f"folder-{index}", values=(folder_path,))

    def on_add_managed_folder(self):
        folder_path = self.selected_folder_var.get().strip()
        if not folder_path:
            messagebox.showerror("Missing folder", "Select a folder before adding it as managed.")
            return

        if not os.path.isdir(folder_path):
            messagebox.showerror("Invalid folder", "Selected folder path does not exist.")
            return

        normalized_folder = self._normalize_path(folder_path)
        if normalized_folder in self.managed_folders:
            self.log(f"Folder already managed: {normalized_folder}")
            return

        self.managed_folders.append(normalized_folder)
        self.managed_folders.sort()
        self._refresh_managed_folders_tree()
        self._save_local_state()
        self.log(f"Added managed folder: {normalized_folder}")

    def on_remove_managed_folder(self):
        selected = self.managed_folders_tree.selection()
        if not selected:
            messagebox.showerror("No selection", "Select a managed folder row to remove.")
            return

        selected_id = selected[0]
        values = self.managed_folders_tree.item(selected_id, "values")
        if not values:
            return
        folder_path = values[0]

        self.managed_folders = [folder for folder in self.managed_folders if folder != folder_path]
        self._refresh_managed_folders_tree()
        self._save_local_state()
        self.log(f"Removed managed folder: {folder_path}")

    def _queue_has_path(self, path_key):
        for item in self.upload_queue_items:
            if item.get("pathKey") != path_key:
                continue
            if item.get("status") in {"QUEUED", "UPLOADING"}:
                return True
        return False

    def _queue_find_item(self, path_key, status):
        for item in self.upload_queue_items:
            if item.get("pathKey") == path_key and item.get("status") == status:
                return item
        return None

    def on_run_sync_job(self):
        headers = self._headers()
        if not headers:
            return

        if self.upload_queue_running:
            self.log("Upload queue is already running.")
            return

        if not self.managed_folders:
            messagebox.showerror("No managed folders", "Add at least one managed folder before running sync.")
            return

        added_count = 0
        skipped_known_count = 0
        skipped_video_count = 0
        duplicate_candidate_count = 0
        missing_folder_count = 0
        seen_hashes_this_scan = set()

        for managed_folder in self.managed_folders:
            if not os.path.isdir(managed_folder):
                missing_folder_count += 1
                self.log(f"Managed folder not found, skipping: {managed_folder}")
                continue

            for root_dir, _, files in os.walk(managed_folder):
                for file_name in files:
                    if self._is_sync_video_file(file_name):
                        file_path = os.path.join(root_dir, file_name)
                        path_key = self._normalize_path(file_path)
                        reason = "video upload disabled by sync policy"
                        skipped_video_count += 1

                        existing_skip = self._queue_find_item(path_key, "SKIPPED_VIDEO")
                        if existing_skip:
                            existing_skip["message"] = reason
                            self._queue_update_item(existing_skip["photoId"], "SKIPPED_VIDEO", reason)
                        else:
                            queue_item = {
                                "filePath": file_path,
                                "fileName": file_name,
                                "photoId": uuid.uuid4().hex,
                                "status": "SKIPPED_VIDEO",
                                "message": reason,
                                "pathKey": path_key,
                            }
                            self.upload_queue_items.append(queue_item)
                            self._queue_insert_item(queue_item)
                        continue

                    if not self._is_sync_image_file(file_name):
                        continue

                    file_path = os.path.join(root_dir, file_name)
                    path_key = self._normalize_path(file_path)
                    signature = self._build_file_signature(file_path)
                    if not signature:
                        continue

                    content_hash = self._compute_content_hash(file_path)
                    if not content_hash:
                        continue

                    known_entry = self.synced_files.get(path_key)
                    if known_entry and known_entry.get("signature") == signature:
                        skipped_known_count += 1
                        continue

                    if content_hash in seen_hashes_this_scan:
                        duplicate_candidate_count += 1
                    seen_hashes_this_scan.add(content_hash)

                    if self._queue_has_path(path_key):
                        continue

                    queue_item = {
                        "filePath": file_path,
                        "fileName": file_name,
                        "photoId": uuid.uuid4().hex,
                        "status": "QUEUED",
                        "message": "sync-new",
                        "pathKey": path_key,
                        "signature": signature,
                        "contentHash": content_hash,
                        "subjects": self._build_subjects_for_file(file_path, managed_folder),
                    }
                    self.upload_queue_items.append(queue_item)
                    self._queue_insert_item(queue_item)
                    added_count += 1

        self.log(
            "Sync scan complete. "
            f"Queued new files: {added_count}, Already synced: {skipped_known_count}, "
            f"Skipped videos: {skipped_video_count}, Duplicate candidates: {duplicate_candidate_count}, "
            f"Missing folders: {missing_folder_count}"
        )

        queued_items = [item for item in self.upload_queue_items if item.get("status") == "QUEUED"]
        if not queued_items:
            self.log("No queued files to upload after sync scan.")
            return

        max_parallel = self._get_queue_parallelism()
        if max_parallel is None:
            return

        if duplicate_candidate_count > 0 and max_parallel > 1:
            self.log("Duplicate candidates detected; running sync queue in serial mode for deterministic dedupe linking.")
            max_parallel = 1

        self.upload_queue_running = True
        self._run_in_thread(self._run_upload_queue_flow, headers, max_parallel)

    def on_enqueue_folder(self):
        folder_path = self.selected_folder_var.get().strip()
        if not folder_path:
            messagebox.showerror("Missing folder", "Select a folder to enqueue media files.")
            return

        if not os.path.isdir(folder_path):
            messagebox.showerror("Invalid folder", "Selected folder path does not exist.")
            return

        queued_count = 0
        for root_dir, _, files in os.walk(folder_path):
            for file_name in files:
                extension = os.path.splitext(file_name)[1].lower()
                if extension not in SUPPORTED_MEDIA_EXTENSIONS:
                    continue

                file_path = os.path.join(root_dir, file_name)
                queue_item = {
                    "filePath": file_path,
                    "fileName": file_name,
                    "photoId": uuid.uuid4().hex,
                    "status": "QUEUED",
                    "message": "",
                    "pathKey": self._normalize_path(file_path),
                    "signature": self._build_file_signature(file_path),
                    "contentHash": self._compute_content_hash(file_path),
                    "subjects": self._build_subjects_for_file(file_path, folder_path),
                }
                self.upload_queue_items.append(queue_item)
                self._queue_insert_item(queue_item)
                queued_count += 1

        if queued_count == 0:
            self.log("No supported media files found in selected folder.")
            return

        self.log(f"Queued {queued_count} files for upload.")

    def on_retry_failed_queue_items(self):
        if self.upload_queue_running:
            self.log("Queue is running; retry can be applied after current run completes.")
            return

        retried = 0
        for item in self.upload_queue_items:
            if item.get("status") == "FAILED":
                item["status"] = "QUEUED"
                item["message"] = ""
                self._queue_update_item(item["photoId"], "QUEUED", "")
                retried += 1

        if retried == 0:
            self.log("No failed queue items to retry.")
            return

        self.log(f"Marked {retried} failed items as QUEUED.")

    def on_cancel_queued_items(self):
        cancelled = 0
        for item in self.upload_queue_items:
            if item.get("status") == "QUEUED":
                item["status"] = "CANCELLED"
                item["message"] = "cancelled by user"
                self._queue_update_item(item["photoId"], "CANCELLED", "cancelled by user")
                cancelled += 1

        if cancelled == 0:
            self.log("No queued items available to cancel.")
            return

        self.log(f"Cancelled {cancelled} queued items.")

    def _get_queue_parallelism(self):
        value_raw = self.queue_parallelism_var.get().strip() or str(DEFAULT_QUEUE_PARALLELISM)
        if not value_raw.isdigit():
            messagebox.showerror(
                "Invalid parallelism",
                f"Parallel uploads must be a number between 1 and {MAX_QUEUE_PARALLELISM}.",
            )
            return None

        value = int(value_raw)
        if value < 1 or value > MAX_QUEUE_PARALLELISM:
            messagebox.showerror(
                "Invalid parallelism",
                f"Parallel uploads must be a number between 1 and {MAX_QUEUE_PARALLELISM}.",
            )
            return None

        return value

    def on_run_upload_queue(self):
        if self.upload_queue_running:
            self.log("Upload queue is already running.")
            return

        headers = self._headers()
        if not headers:
            return

        queued_items = [item for item in self.upload_queue_items if item.get("status") == "QUEUED"]
        if not queued_items:
            self.log("No queued files to upload.")
            return

        max_parallel = self._get_queue_parallelism()
        if max_parallel is None:
            return

        self.upload_queue_running = True
        self._run_in_thread(self._run_upload_queue_flow, headers, max_parallel)

    def _queue_insert_item(self, item):
        self._schedule_queue_refresh()

    def _schedule_queue_refresh(self):
        if self._queue_refresh_scheduled:
            return
        self._queue_refresh_scheduled = True
        self.root.after(50, self._refresh_queue_tree_view)

    def _refresh_queue_tree_view(self):
        self._queue_refresh_scheduled = False

        for item_id in self.queue_tree.get_children():
            self.queue_tree.delete(item_id)

        status_filter = (self.queue_status_filter_var.get() or "ALL").strip().upper()
        search_filter = (self.queue_search_filter_var.get() or "").strip().lower()

        for item in self.upload_queue_items:
            file_path = item.get("filePath") or ""
            file_name = item.get("fileName") or os.path.basename(file_path)
            item["fileName"] = file_name
            status = (item.get("status") or "").upper()
            message = item.get("message") or ""

            if status_filter != "ALL" and status != status_filter:
                continue

            if search_filter and search_filter not in file_name.lower() and search_filter not in message.lower():
                continue

            self.queue_tree.insert(
                "",
                "end",
                iid=item["photoId"],
                values=(file_name, status, message),
            )

    def _queue_update_item(self, photo_id, status, message=""):
        def _apply_update():
            self._schedule_queue_refresh()

        self.root.after(0, _apply_update)

    def on_apply_queue_filters(self):
        self._schedule_queue_refresh()

    def on_reset_queue_filters(self):
        self.queue_status_filter_var.set("ALL")
        self.queue_search_filter_var.set("")
        self._schedule_queue_refresh()

    def _clear_queue_items_by_status(self, statuses):
        status_set = {status.upper() for status in statuses}
        before = len(self.upload_queue_items)
        self.upload_queue_items = [
            item for item in self.upload_queue_items if (item.get("status") or "").upper() not in status_set
        ]
        removed = before - len(self.upload_queue_items)
        self._schedule_queue_refresh()
        self.log(f"Removed {removed} queue rows for statuses: {', '.join(sorted(status_set))}")

    def on_clear_completed_queue_items(self):
        self._clear_queue_items_by_status({"COMPLETED"})

    def on_clear_failed_queue_items(self):
        self._clear_queue_items_by_status({"FAILED"})

    def on_clear_skipped_queue_items(self):
        self._clear_queue_items_by_status({"SKIPPED_VIDEO"})

    @staticmethod
    def _extract_error_message(response_body, fallback_message):
        if isinstance(response_body, dict):
            error_text = response_body.get("error")
            if error_text:
                return str(error_text)
            raw_text = response_body.get("raw")
            if raw_text:
                return str(raw_text)[:180]
        return fallback_message

    def _upload_one_file(self, headers, file_path, photo_id, original_file_name, content_type, subjects=None, content_hash=None):
        payload = {
            "photoId": photo_id,
            "contentType": content_type,
            "originalFileName": original_file_name,
        }
        if subjects:
            payload["subjects"] = subjects
        if content_hash:
            payload["contentHash"] = content_hash
        upload_init_url = f"{self.api_base_url_var.get().rstrip('/')}/photos/upload-url"

        init_response = requests.post(upload_init_url, headers=headers, json=payload, timeout=30)
        init_body = self._safe_json(init_response)
        self.log(f"POST /photos/upload-url -> {init_response.status_code} ({original_file_name})")
        if init_response.status_code != 200:
            error_message = self._extract_error_message(init_body, f"upload-init failed ({init_response.status_code})")
            return False, error_message, False

        upload_required = init_body.get("uploadRequired")
        if upload_required is False:
            return True, "deduplicated-link", True

        upload_url = init_body.get("uploadUrl")
        if not upload_url:
            return False, "uploadUrl missing in response", False

        with open(file_path, "rb") as source:
            put_response = requests.put(
                upload_url,
                data=source,
                headers={"Content-Type": content_type},
                timeout=180,
            )

        self.log(f"PUT signed-url -> {put_response.status_code} ({original_file_name})")
        if put_response.status_code not in (200, 201):
            return False, f"upload-bytes failed ({put_response.status_code})", False

        upload_complete_url = f"{self.api_base_url_var.get().rstrip('/')}/photos/upload-complete"
        complete_response = requests.post(
            upload_complete_url,
            headers=headers,
            json={"photoId": photo_id},
            timeout=30,
        )
        complete_body = self._safe_json(complete_response)
        self.log(f"POST /photos/upload-complete -> {complete_response.status_code} ({original_file_name})")
        if complete_response.status_code != 200:
            error_message = self._extract_error_message(complete_body, f"upload-complete failed ({complete_response.status_code})")
            return False, error_message, False

        return True, "completed", False

    def _run_upload_queue_flow(self, headers, max_parallel):
        queued_items = [item for item in self.upload_queue_items if item.get("status") == "QUEUED"]
        self.log(f"Starting folder upload queue with {len(queued_items)} files (parallel={max_parallel})...")

        stats = {
            "success": 0,
            "failed": 0,
            "cancelled": 0,
            "deduplicated": 0,
        }

        pending_items = list(queued_items)

        try:
            def _worker_loop():
                while True:
                    with self.upload_queue_lock:
                        if not pending_items:
                            return
                        item = pending_items.pop(0)

                    file_path = item["filePath"]
                    file_name = item["fileName"]
                    photo_id = item["photoId"]

                    with self.upload_queue_lock:
                        if item.get("status") != "QUEUED":
                            if item.get("status") == "CANCELLED":
                                stats["cancelled"] += 1
                            continue
                        item["status"] = "UPLOADING"
                        item["message"] = ""

                    self._queue_update_item(photo_id, "UPLOADING", "")

                    guessed_type, _ = mimetypes.guess_type(file_path)
                    content_type = guessed_type or "application/octet-stream"

                    try:
                        ok, message, deduplicated = self._upload_one_file(
                            headers=headers,
                            file_path=file_path,
                            photo_id=photo_id,
                            original_file_name=file_name,
                            content_type=content_type,
                            subjects=item.get("subjects"),
                            content_hash=item.get("contentHash"),
                        )
                        with self.upload_queue_lock:
                            if ok:
                                item["status"] = "COMPLETED"
                                item["message"] = message
                                stats["success"] += 1
                                if deduplicated:
                                    stats["deduplicated"] += 1
                                path_key = item.get("pathKey")
                                signature = item.get("signature")
                                content_hash = item.get("contentHash")
                                if path_key and signature:
                                    self.synced_files[path_key] = {
                                        "signature": signature,
                                        "contentHash": content_hash,
                                        "photoId": photo_id,
                                        "uploadedAt": datetime.now(timezone.utc).isoformat(),
                                    }
                                status = "COMPLETED"
                                status_message = message
                            else:
                                item["status"] = "FAILED"
                                item["message"] = message
                                stats["failed"] += 1
                                status = "FAILED"
                                status_message = message
                        self._queue_update_item(photo_id, status, status_message)
                        if not ok:
                            self.log(f"Queue item failed ({file_name}): {message}")
                    except Exception as error:
                        error_message = str(error)
                        with self.upload_queue_lock:
                            item["status"] = "FAILED"
                            item["message"] = error_message
                            stats["failed"] += 1
                        self._queue_update_item(photo_id, "FAILED", error_message)
                        self.log(f"Queue item failed ({file_name}): {error_message}")

            with ThreadPoolExecutor(max_workers=max_parallel) as executor:
                futures = [executor.submit(_worker_loop) for _ in range(max_parallel)]
                for future in futures:
                    future.result()

            self.log(
                "Folder upload queue complete. "
                f"Success: {stats['success']}, Failed: {stats['failed']}, "
                f"Deduplicated: {stats['deduplicated']}, Cancelled: {stats['cancelled']}"
            )
            self._save_local_state()
            self.root.after(0, self.on_list_photos)
        finally:
            self.upload_queue_running = False

    def _require_auth(self):
        self._refresh_google_token_if_needed()

        token = self.id_token_var.get().strip()
        if not token:
            messagebox.showerror(
                "Missing token",
                "Sign in with Google or paste your Google ID token before calling the API.",
            )
            return None

        if token.lower().startswith("bearer "):
            messagebox.showerror("Invalid token", "Paste only the raw ID token (starts with eyJ...), without 'Bearer '.")
            return None

        if any(ch in token for ch in ["\n", "\r", "\t"]):
            messagebox.showerror("Invalid token", "Token must be a single line with no extra text or logs.")
            return None

        if " " in token:
            messagebox.showerror("Invalid token", "Token appears to contain spaces. Paste only the raw token value.")
            return None

        if not re.match(r"^[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+$", token):
            messagebox.showerror("Invalid token", "Token must be a JWT in header.payload.signature format.")
            return None

        if not token.startswith("eyJ"):
            messagebox.showerror("Invalid token", "Expected a Google ID token starting with 'eyJ'.")
            return None

        return token

    def _headers(self):
        token = self._require_auth()
        if not token:
            return None
        return {"Authorization": f"Bearer {token}"}

    def on_upload(self):
        headers = self._headers()
        if not headers:
            return

        file_path = self.selected_file_var.get().strip()
        photo_id = self.photo_id_var.get().strip()
        content_type = self.content_type_var.get().strip() or "application/octet-stream"

        if not file_path:
            messagebox.showerror("Missing file", "Select a file to upload.")
            return

        if not os.path.isfile(file_path):
            messagebox.showerror("Invalid file", "Selected file path does not exist.")
            return

        if not photo_id:
            messagebox.showerror("Missing photo ID", "Enter a photo ID.")
            return

        payload = {
            "photoId": photo_id,
            "contentType": content_type,
            "originalFileName": self.selected_file_name_var.get().strip() or os.path.basename(file_path),
            "contentHash": self._compute_content_hash(file_path),
            "subjects": self._build_subjects_for_file(file_path),
        }
        upload_init_url = f"{self.api_base_url_var.get().rstrip('/')}/photos/upload-url"

        self._run_in_thread(self._upload_flow, upload_init_url, headers, payload, file_path, content_type)

    def _upload_flow(self, upload_init_url, headers, payload, file_path, content_type):
        try:
            self.log("Starting upload...")
            ok, message, deduplicated = self._upload_one_file(
                headers=headers,
                file_path=file_path,
                photo_id=payload["photoId"],
                original_file_name=payload["originalFileName"],
                content_type=content_type,
                subjects=payload.get("subjects"),
                content_hash=payload.get("contentHash"),
            )

            if ok:
                if deduplicated:
                    self.log("Upload linked to existing content hash (deduplicated). Refreshing photo list...")
                else:
                    self.log("Upload finalized. Refreshing photo list...")
                self.download_photo_id_var.set(payload["photoId"])
                self.root.after(0, self.on_list_photos)
            else:
                self.log(f"Upload failed: {message}")
        except requests.RequestException as error:
            self.log(f"Network error: {error}")
        except Exception as error:
            self.log(f"Unexpected error: {error}")

    def on_get_download_url(self):
        headers = self._headers()
        if not headers:
            return

        photo_id = self.download_photo_id_var.get().strip()
        if not photo_id:
            messagebox.showerror("Missing photo ID", "Enter a photo ID for download URL lookup.")
            return

        endpoint = f"{self.api_base_url_var.get().rstrip('/')}/photos/{photo_id}/download-url"
        self._run_in_thread(self._download_lookup_flow, endpoint, headers, photo_id)

    def _download_lookup_flow(self, endpoint, headers, photo_id):
        try:
            self.log(f"Requesting download URL for photoId={photo_id}...")
            response = requests.get(endpoint, headers=headers, timeout=30)
            body = self._safe_json(response)
            self.log(f"GET /photos/{{photoId}}/download-url -> {response.status_code}")
            self.log(pretty_json(body))
        except requests.RequestException as error:
            self.log(f"Network error: {error}")
        except Exception as error:
            self.log(f"Unexpected error: {error}")

    def on_use_selected_photo(self):
        selected_photo = self._get_selected_photo()
        if not selected_photo:
            messagebox.showerror("No selection", "Select a photo row first.")
            return

        photo_id = selected_photo.get("photoId")
        if photo_id:
            self.download_photo_id_var.set(photo_id)
            self.log(f"Selected photo for download lookup: {photo_id}")

    def on_open_selected_image(self):
        selected_photo = self._get_selected_photo()
        if not selected_photo:
            messagebox.showerror("No selection", "Select a photo row first.")
            return

        content_type = (selected_photo.get("contentType") or "").lower()
        if content_type and not content_type.startswith("image/"):
            messagebox.showerror("Not an image", f"Selected item is '{content_type}', not an image.")
            return

        headers = self._headers()
        if not headers:
            return

        photo_id = selected_photo.get("photoId")
        endpoint = f"{self.api_base_url_var.get().rstrip('/')}/photos/{photo_id}/download-url"
        self._run_in_thread(self._open_selected_image_flow, endpoint, headers, photo_id)

    def _open_selected_image_flow(self, endpoint, headers, photo_id):
        try:
            self.log(f"Requesting download URL for selected photoId={photo_id}...")
            response = requests.get(endpoint, headers=headers, timeout=30)
            body = self._safe_json(response)
            self.log(f"GET /photos/{{photoId}}/download-url -> {response.status_code}")
            self.log(pretty_json(body))

            if response.status_code != 200:
                return

            download_url = body.get("downloadUrl")
            if not download_url:
                self.log("downloadUrl missing in response.")
                return

            opened = webbrowser.open(download_url)
            if opened:
                self.log(f"Opened image in default browser for photoId={photo_id}.")
            else:
                self.log("Could not open browser automatically. Copy downloadUrl from output.")
        except requests.RequestException as error:
            self.log(f"Network error: {error}")
        except Exception as error:
            self.log(f"Unexpected error: {error}")

    def on_list_photos(self):
        headers = self._headers()
        if not headers:
            return

        limit_raw = self.list_limit_var.get().strip() or "20"
        if not limit_raw.isdigit() or int(limit_raw) < 1 or int(limit_raw) > 100:
            messagebox.showerror("Invalid limit", "Limit must be a number between 1 and 100.")
            return

        params = {"limit": limit_raw}
        next_token = self.list_next_token_var.get().strip()
        if next_token:
            params["nextToken"] = next_token

        endpoint = f"{self.api_base_url_var.get().rstrip('/')}/photos"
        self._run_in_thread(self._list_photos_flow, endpoint, headers, params)

    def _list_photos_flow(self, endpoint, headers, params):
        try:
            self.log("Requesting photo list...")
            response = requests.get(endpoint, headers=headers, params=params, timeout=30)
            body = self._safe_json(response)
            self.log(f"GET /photos -> {response.status_code}")
            self.log(pretty_json(body))

            if response.status_code != 200:
                return

            photos = body.get("photos") or []
            next_token = body.get("nextToken") or ""
            self.list_next_token_var.set(next_token)
            self.root.after(0, self._refresh_photos_table, photos)

            if photos:
                first_photo_id = photos[0].get("photoId")
                if first_photo_id:
                    self.download_photo_id_var.set(first_photo_id)
                    self.log(f"Auto-selected first photoId for download lookup: {first_photo_id}")
            else:
                self.log("No photos returned for this page.")
        except requests.RequestException as error:
            self.log(f"Network error: {error}")
        except Exception as error:
            self.log(f"Unexpected error: {error}")

    def on_search_photos(self):
        headers = self._headers()
        if not headers:
            return

        query = self.search_query_var.get().strip()
        if not query:
            messagebox.showerror("Missing query", "Enter a search query (filename or subjects).")
            return

        limit_raw = self.search_limit_var.get().strip() or "20"
        if not limit_raw.isdigit() or int(limit_raw) < 1 or int(limit_raw) > 100:
            messagebox.showerror("Invalid limit", "Limit must be a number between 1 and 100.")
            return

        params = {"q": query, "limit": limit_raw}
        endpoint = f"{self.api_base_url_var.get().rstrip('/')}/photos/search"
        self._run_in_thread(self._search_photos_flow, endpoint, headers, params)

    def _search_photos_flow(self, endpoint, headers, params):
        try:
            self.log(f"Searching photos with query: {params.get('q')}...")
            response = requests.get(endpoint, headers=headers, params=params, timeout=30)
            body = self._safe_json(response)
            self.log(f"GET /photos/search -> {response.status_code}")
            self.log(pretty_json(body))

            if response.status_code != 200:
                if response.status_code == 404:
                    self.log("Search endpoint not yet available. Please ensure backend is deployed.")
                return

            photos = body.get("photos") or []
            self.root.after(0, self._refresh_photos_table, photos)

            if photos:
                first_photo_id = photos[0].get("photoId")
                if first_photo_id:
                    self.download_photo_id_var.set(first_photo_id)
                    self.log(f"Auto-selected first photoId for download lookup: {first_photo_id}")
                self.log(f"Found {len(photos)} matching photos.")
            else:
                self.log("No photos found matching the search criteria.")
        except requests.RequestException as error:
            self.log(f"Network error: {error}")
        except Exception as error:
            self.log(f"Unexpected error: {error}")

    def _refresh_photos_table(self, photos):
        self.latest_photos = photos
        for item_id in self.photos_tree.get_children():
            self.photos_tree.delete(item_id)

        for index, item in enumerate(photos):
            self.photos_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    item.get("fileName") or "",
                    item.get("photoId") or "",
                    item.get("contentType") or "",
                    item.get("createdAt") or "",
                ),
            )

        if photos:
            self.photos_tree.selection_set("0")

    def _get_selected_photo(self):
        selected = self.photos_tree.selection()
        if not selected:
            return None
        index = int(selected[0])
        if index < 0 or index >= len(self.latest_photos):
            return None
        return self.latest_photos[index]

    def _run_in_thread(self, fn, *args):
        thread = threading.Thread(target=fn, args=args, daemon=True)
        thread.start()

    @staticmethod
    def _safe_json(response):
        try:
            return response.json()
        except Exception:
            return {"raw": response.text[:4000]}


def main():
    root = tk.Tk()
    app = MillerPicDesktopApp(root)
    app.log("Sign in with Google or paste your Google ID token, then start with Upload Photo.")
    root.mainloop()


if __name__ == "__main__":
    main()
