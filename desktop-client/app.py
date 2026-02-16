import json
import mimetypes
import os
import re
import threading
import uuid
import webbrowser
from datetime import datetime, timezone
from tkinter import END, BOTH, LEFT, RIGHT, X, filedialog, messagebox, ttk
import tkinter as tk

from google.auth.transport.requests import Request as GoogleAuthRequest
from google_auth_oauthlib.flow import InstalledAppFlow
import requests


DEFAULT_API_BASE_URL = "https://09ew2nqn27.execute-api.us-east-1.amazonaws.com"
DEFAULT_OAUTH_CLIENT_FILE = os.path.join(os.path.dirname(__file__), "google_oauth_client.json")
GOOGLE_OAUTH_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


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
        self.content_type_var = tk.StringVar(value="image/webp")
        self.photo_id_var = tk.StringVar()
        self.download_photo_id_var = tk.StringVar()
        self.list_limit_var = tk.StringVar(value="20")
        self.list_next_token_var = tk.StringVar()
        self.latest_photos = []
        self.google_credentials = None

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

        download_frame = ttk.LabelFrame(container, text="Get Download URL", padding=10)
        download_frame.pack(fill=X, pady=(12, 0))

        ttk.Label(download_frame, text="Photo ID").grid(row=0, column=0, sticky="w")
        ttk.Entry(download_frame, textvariable=self.download_photo_id_var, width=40).grid(
            row=1, column=0, sticky="w", padx=(0, 10)
        )
        ttk.Button(download_frame, text="Fetch Download URL", command=self.on_get_download_url).grid(
            row=1, column=1, sticky="w"
        )

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
        }
        upload_init_url = f"{self.api_base_url_var.get().rstrip('/')}/photos/upload-url"

        self._run_in_thread(self._upload_flow, upload_init_url, headers, payload, file_path, content_type)

    def _upload_flow(self, upload_init_url, headers, payload, file_path, content_type):
        try:
            self.log("Starting upload init request...")
            init_response = requests.post(upload_init_url, headers=headers, json=payload, timeout=30)
            init_body = self._safe_json(init_response)
            self.log(f"POST /photos/upload-url -> {init_response.status_code}")
            self.log(pretty_json(init_body))

            if init_response.status_code != 200:
                return

            upload_url = init_body.get("uploadUrl")
            if not upload_url:
                self.log("uploadUrl missing in response.")
                return

            with open(file_path, "rb") as source:
                self.log("Uploading file to signed URL...")
                put_response = requests.put(
                    upload_url,
                    data=source,
                    headers={"Content-Type": content_type},
                    timeout=180,
                )
            self.log(f"PUT signed-url -> {put_response.status_code}")
            if put_response.status_code in (200, 201):
                self.log("Upload complete.")
                self.download_photo_id_var.set(payload["photoId"])
            else:
                self.log(put_response.text[:2000])
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
