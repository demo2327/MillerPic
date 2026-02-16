# MillerPic Desktop Client (MVP)

Simple Windows desktop app for testing your deployed API without Postman.

## What this does

- Paste your Google ID token once
- Pick a file and call `POST /upload`
- Upload the file to the returned signed S3 URL
- Call `GET /download/{photoId}` to fetch a signed download URL
- Call `GET /photos` to list your uploaded photos (with optional pagination token)
- Select a listed image and open it in your default browser

## Prerequisites

- Python 3.10+
- Deployed backend API
- Valid Google ID token (`eyJ...`)

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
2. Paste your Google ID token in the token field.
3. Click **Browse** and choose a photo/video.
4. Click **Upload Selected File**.
5. After successful upload, click **Fetch Download URL**.
6. Copy the returned `downloadUrl` to your browser.
7. Use **List Photos** to retrieve your photos and paginate with `nextToken`.
8. Select a row and click **Open Selected Image**.

## Notes

- This is an MVP client for upload/download API verification.
- The `Content-Type` sent to signed S3 upload must match what is used in the upload init call.
- If upload init returns 401/403, your token is missing/expired/not verified.
- Token field must contain only the raw single-line ID token (`eyJ...`), not `Bearer ...` and not logs.
