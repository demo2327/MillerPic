# MillerPic Manual Testing (No PowerShell)

## 1) Use Postman Desktop
- Import `MillerPic.postman_collection.json`
- Import `MillerPic.postman_environment.json`
- Select environment **MillerPic Local**

## 2) Get a Google ID Token (GUI)
In Google Cloud Console for your OAuth client, add this redirect URI if missing:
- `https://oauth.pstmn.io/v1/callback`

Then in Postman:
1. Open request **Upload URL**
2. Authorization tab:
   - Type: **OAuth 2.0**
   - Grant Type: **Authorization Code (With PKCE)**
   - Auth URL: `https://accounts.google.com/o/oauth2/v2/auth`
   - Access Token URL: `https://oauth2.googleapis.com/token`
   - Client ID: `367922653610-kagqhagn7ktigsvuemltqn6cqcvo0pad.apps.googleusercontent.com`
   - Scope: `openid email profile`
   - Callback URL: `https://oauth.pstmn.io/v1/callback`
   - Client Authentication: `Send client credentials in body` (or none when PKCE is available)
3. Click **Get New Access Token** and complete Google sign-in.
4. In token response, copy `id_token` and set environment variable `id_token`.

## 3) Test API
1. Set `photo_id` in environment (for example `photo-gui-001`)
2. Run **Upload URL** (expect HTTP 200)
3. Run **Download URL** (expect HTTP 200)

## 4) Optional direct file upload in Postman
- Use returned `uploadUrl` with a separate PUT request in Postman to upload a small `.webp` file.
- Re-run **Download URL** and open returned URL.

## Expected
- Without token: 401
- With valid Google ID token from configured audience: 200
