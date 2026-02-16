# MillerPic Desktop Client (MVP)

Simple Windows desktop app for testing your deployed API without Postman.

## What this does

- Sign in with Google from the desktop app (or paste token manually)
- Pick a file and call `POST /upload`
- Upload the file to the returned signed S3 URL
- Call `GET /download/{photoId}` to fetch a signed download URL
- Call `GET /photos` to list your uploaded photos (with optional pagination token)
- Select a listed image and open it in your default browser
- Persist managed folders and run incremental sync for new image files
- Auto-populate subjects from folder hierarchy and image EXIF date/geolocation when available

## Prerequisites

- Python 3.10+
- Deployed backend API
- Google OAuth Desktop client JSON at `desktop-client/google_oauth_client.json`

## Run

```bash
cd desktop-client
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Usage

1. Keep API Base URL as your deployed URL (already prefilled).
2. Click **Sign in with Google** (recommended).
3. If needed, you can still paste a valid Google ID token manually.
3. Click **Browse** and choose a photo/video.
4. Click **Upload Selected File**.
5. After successful upload, click **Fetch Download URL**.
6. Copy the returned `downloadUrl` to your browser.
7. Use **List Photos** to retrieve your photos and paginate with `nextToken`.
8. Select a row and click **Open Selected Image**.
9. For folder sync, choose a folder, click **Add Managed Folder**, then click **Run Sync Job**.
10. Videos detected during sync are marked as skipped and are not uploaded.
11. Sync uploads add metadata subjects automatically (folder labels + EXIF date/geo when present).
12. Sync reports duplicate detections and links duplicate content by hash without re-uploading bytes.

## Notes

- This is an MVP client for upload/download API verification.
- The `Content-Type` sent to signed S3 upload must match what is used in the upload init call.
- If upload init returns 401/403, your token is missing/expired/not verified.
- Token field must contain only the raw single-line ID token (`eyJ...`), not `Bearer ...` and not logs.
- For sign-in setup, create a Google OAuth client of type **Desktop app** and save the downloaded JSON as `desktop-client/google_oauth_client.json`.
- Optional: set `MILLERPIC_GOOGLE_OAUTH_CLIENT_FILE` to point to a custom OAuth client JSON path.
- Optional: set `MILLERPIC_DESKTOP_STATE_FILE` to customize where managed-folder sync state is stored.
