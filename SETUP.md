# Research Tracker — Complete Setup Guide

## What you'll need
- A free Google account
- A free GitHub account → github.com
- A free Vercel account → vercel.com

---

## STEP 1 — Get your Google API credentials (takes ~10 minutes)

### 1a. Create a Google Cloud Project
1. Go to → **https://console.cloud.google.com**
2. Click **"Select a project"** (top left) → **"New Project"**
3. Project name: `Research Tracker` → click **Create**
4. Make sure the new project is selected in the top dropdown

### 1b. Enable the required APIs (all free)
1. Left menu → **"APIs & Services"** → **"Library"**
2. Search **"Google Sheets API"** → click it → click the blue **Enable** button
3. Search **"Google Drive API"** → click it → click **Enable**

### 1c. Set up the OAuth consent screen
1. Left menu → **"APIs & Services"** → **"OAuth consent screen"**
2. Choose **External** → click **Create**
3. Fill in:
   - App name: `Research Tracker`
   - User support email: your Gmail address
   - Developer contact email: your Gmail address
4. Click **Save and Continue** through all the steps (no need to add scopes manually)
5. On the last screen, click **Back to Dashboard**
6. Under "Test users", click **Add Users** → add your own Gmail address → Save

### 1d. Create OAuth credentials
1. Left menu → **"Credentials"** → **"+ Create Credentials"** → **"OAuth client ID"**
2. Application type: **Web application**
3. Name: `Research Tracker`
4. Under **"Authorised redirect URIs"** click Add URI and add:
   ```
   http://localhost:5000/auth/callback
   ```
   (You will add your Vercel URL here later — see Step 4)
5. Click **Create**
6. A popup appears — click **"Download JSON"**
7. The downloaded file is named something like `client_secret_xxx.json`
8. **Rename it to exactly:** `client_secrets.json`

### 1e. Note the contents for Vercel
Open `client_secrets.json` in a text editor, select ALL the text, and copy it.
You will need to paste this into Vercel in Step 3.

---

## STEP 2 — Create your Google Spreadsheet
1. Go to → **https://sheets.google.com**
2. Click **"Blank"** to create a new spreadsheet
3. Name it: `Research Tracker Data`
4. Copy the **Spreadsheet ID** from the URL bar:
   ```
   https://docs.google.com/spreadsheets/d/  ←THIS PART→  /edit
   ```
   Example ID: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms`

The app will automatically create three tabs when you first log in:
- **Papers** — all your paper data
- **Activity** — change log
- **Journals** — target journal list (pre-loaded with 14 top journals)

---

## STEP 3 — Upload to GitHub

### 3a. Create a GitHub account (if you don't have one)
Go to **https://github.com** → Sign up (free)

### 3b. Create a new repository
1. Click the **+** button (top right) → **"New repository"**
2. Repository name: `research-tracker`
3. Keep it **Public** (required for free Vercel deployment)
4. Click **"Create repository"**

### 3c. Upload all files
1. On your new empty repository page, click **"uploading an existing file"** link
2. Drag and drop ALL files from your project folder:
   ```
   app.py
   config.py
   sheets_service.py
   requirements.txt
   vercel.json
   .gitignore
   .env.example
   SETUP.md
   static/
     css/
       style.css
     js/
       main.js
   templates/
     base.html
     login.html
     dashboard.html
     papers.html
     paper_detail.html
     journals.html
     timeline.html
     timeline.html
     404.html
     _modal_add_paper.html
   ```
   ⚠️ **DO NOT upload:** `.env` or `client_secrets.json` (these contain your secrets)

3. Scroll down, click **"Commit changes"**

---

## STEP 4 — Deploy on Vercel

### 4a. Sign up for Vercel
Go to **https://vercel.com** → click **"Sign up"** → choose **"Continue with GitHub"** → authorise Vercel

### 4b. Import your GitHub repository
1. On the Vercel dashboard, click **"Add New..."** → **"Project"**
2. Find your `research-tracker` repository → click **"Import"**
3. Leave all settings as default
4. **DO NOT click Deploy yet** — first add environment variables below

### 4c. Add Environment Variables (most important step)
Before clicking Deploy, click **"Environment Variables"** and add these 3 variables:

| Variable Name | Value |
|---|---|
| `FLASK_SECRET_KEY` | A long random string (generate below) |
| `SPREADSHEET_ID` | Your Sheet ID from Step 2 |
| `GOOGLE_CREDENTIALS` | The entire contents of `client_secrets.json` |

**How to generate FLASK_SECRET_KEY:**
```
Go to https://www.uuidgenerator.net/ and copy the UUID,
then paste it twice joined together (gives you a long random string)
```
OR if you have Python installed locally:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**For GOOGLE_CREDENTIALS:**
Open `client_secrets.json`, select all text, paste the entire JSON as the value.
It should start with `{"web":{"client_id":...`

### 4d. Deploy
Click **"Deploy"** — Vercel builds and deploys in about 60 seconds.
You will get a URL like: `https://research-tracker-abc123.vercel.app`

---

## STEP 5 — Update Google OAuth with your Vercel URL

1. Go back to → **https://console.cloud.google.com**
2. Left menu → **"APIs & Services"** → **"Credentials"**
3. Click your OAuth 2.0 Client ID (the pencil/edit button)
4. Under **"Authorised redirect URIs"**, click **"Add URI"** and add:
   ```
   https://YOUR-APP-NAME.vercel.app/auth/callback
   ```
   Replace `YOUR-APP-NAME` with your actual Vercel URL
5. Click **"Save"**

---

## STEP 6 — First Login

1. Open your Vercel URL: `https://research-tracker-xxx.vercel.app`
2. Click **"Continue with Google"**
3. Sign in with the Google account you added as a test user in Step 1c
4. Grant the permissions
5. The app auto-creates all sheet tabs and seeds 14 journals
6. Click **"+ New Paper"** and start tracking! 🎉

---

## File structure (what you upload to GitHub)

```
research-tracker/
├── app.py                    ← Main Flask app (all routes)
├── config.py                 ← Stage definitions, column mappings
├── sheets_service.py         ← Google Sheets read/write layer
├── requirements.txt          ← Python packages
├── vercel.json               ← Vercel deployment config
├── .gitignore                ← Keeps secrets out of GitHub
├── .env.example              ← Template for local development
├── SETUP.md                  ← This guide
├── static/
│   ├── css/style.css         ← All styles (white aesthetic theme)
│   └── js/main.js            ← Client-side helpers
└── templates/
    ├── base.html             ← Master layout (sidebar + topbar)
    ├── login.html            ← Split-screen Google sign-in
    ├── dashboard.html        ← Stats + pipeline + activity
    ├── papers.html           ← Filterable paper list
    ├── paper_detail.html     ← Full paper view + inline edit
    ├── journals.html         ← Target journal list
    ├── timeline.html         ← Timeline + Gantt chart
    ├── 404.html              ← Error page
    └── _modal_add_paper.html ← Reusable add-paper modal
```

---

## Cost breakdown (everything is FREE)

| Service | Free quota | Will you exceed it? |
|---|---|---|
| Google Sheets API | 500 requests/100 seconds | No — a few requests per page |
| Google OAuth | Unlimited sign-ins | Free forever |
| Vercel Hobby plan | 100 GB bandwidth/month | No |
| Google account storage | 15 GB | Your sheet uses a few KB |
| **Total monthly cost** | **$0.00** | |

Google only charges at commercial scale (millions of API calls).
For one researcher tracking papers, you will never hit any limit.
You don't even need to add a payment method to Google Cloud.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "redirect_uri_mismatch" | Add your Vercel URL to Authorised Redirect URIs in Google Cloud Console |
| "Access blocked: app not verified" | Add your Gmail as a Test User in OAuth consent screen |
| "Spreadsheet error" | Check SPREADSHEET_ID environment variable in Vercel settings |
| Blank page after login | Check FLASK_SECRET_KEY is set in Vercel environment variables |
| Login works locally but not on Vercel | Make sure GOOGLE_CREDENTIALS is set (entire JSON, not just the file name) |
| "Error 500" on any page | Check Vercel deployment logs: Vercel dashboard → your project → Deployments → click latest → View Logs |

---

## To run locally (for development/testing)

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# 2. Install packages
pip install -r requirements.txt

# 3. Place client_secrets.json in the project root

# 4. Create .env file
cp .env.example .env
# Edit .env and fill in FLASK_SECRET_KEY and SPREADSHEET_ID

# 5. Run
python app.py

# Open http://localhost:5000
```
