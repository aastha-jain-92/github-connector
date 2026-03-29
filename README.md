# GitHub Cloud Connector

A Django REST Framework connector for GitHub OAuth 2.0 — authenticate users
via GitHub and view their repositories on a live webpage with search, stats,
and one-click access to each repo.

---

## Project Structure

```
github_connector/
├── manage.py
├── requirements.txt
├── .env.example              ← copy this to .env and fill in your values
├── .gitignore
├── github_connector/         ← Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── connector/                ← the GitHub connector app
    ├── exceptions.py         ← custom typed exceptions
    ├── services.py           ← all GitHub API & OAuth logic
    ├── serializers.py        ← response shaping via DRF
    ├── views.py              ← HTTP layer only (thin views)
    ├── urls.py               ← route definitions
    └── templates/
        └── repos.html        ← webpage that displays repositories
```

---

## Setup & Run (Step by Step)

### Step 1 — Create a GitHub OAuth App

1. Go to: https://github.com/settings/developers
2. Click **"New OAuth App"**
3. Fill in:
   - **Application name**: `GitHub Connector` (anything you like)
   - **Homepage URL**: `http://localhost:8000`
   - **Authorization callback URL**: `http://localhost:8000/callback`
4. Click **Register application**
5. Copy the **Client ID** and generate a **Client Secret** — you'll need both below

> ⚠️ The callback URL in the GitHub dashboard must exactly match `GITHUB_REDIRECT_URI` in your `.env`. Even a trailing slash difference will cause an error.

---

### Step 2 — Download & Extract the Project

```bash
unzip github_connector.zip
cd github_connector
```

---

### Step 3 — Create a Virtual Environment

```bash
# Create
python -m venv venv

# Activate (Mac/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

---

### Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 5 — Create Your `.env` File

```bash
# Copy the example file
cp .env.example .env
```

Now open `.env` and fill in your values:

```env
GITHUB_CLIENT_ID=paste_your_client_id_here
GITHUB_CLIENT_SECRET=paste_your_client_secret_here
GITHUB_REDIRECT_URI=http://localhost:8000/callback
SECRET_KEY=generate_using_command_below
DEBUG=True
```

Generate a secure `SECRET_KEY` with this command:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

> ⚠️ Never commit `.env` to Git. It is already listed in `.gitignore`.

---

### Step 6 — Run Migrations

```bash
python manage.py migrate
```

---

### Step 7 — Start the Server

```bash
python manage.py runserver
```

Server is now running at: `http://localhost:8000`

---

## Using the App

### Full Flow Overview

```
Browser visits /login
        ↓
GitHub authorization page (user clicks Authorize)
        ↓
GitHub redirects → /callback?code=XXXXXXXX
        ↓
Server exchanges code for access token
        ↓
Server redirects → /repos-page?token=gho_xxx
        ↓
Webpage stores token in localStorage, cleans the URL
        ↓
Webpage calls /repos API automatically
        ↓
Your repositories appear on screen 🎉
```

---

### Step A — Open the Login Page

Visit this URL in your browser:

```
http://localhost:8000/login
```

You will be redirected to GitHub. Click **"Authorize"**.

---

### Step B — Automatic Redirect to Repos Webpage

After approving on GitHub, the server automatically:
1. Exchanges the code for an access token
2. Redirects you to `/repos-page`
3. The webpage loads and displays all your repositories

No manual token copying needed — everything happens automatically in the browser.

---

### Step C — What You See on the Repos Webpage

- **Stats bar** — total repos, total stars, total forks, private repo count
- **Search box** — filter repos live by name, description, or language
- **Repo cards** — name, visibility (public/private), description, language, stars, forks, last updated time
- **Click any card** — opens that repository on GitHub in a new tab
- **Logout button** — clears the token and returns to the login screen

---

### Step D — Fetch Repos via API (Optional)

You can also call the JSON API directly using curl or Postman.

First get your token from the `/repos-page` URL after login (it appears briefly as `?token=gho_xxx`).

**Your own repos:**
```bash
curl -H "Authorization: Bearer gho_xxxxxxxxxxxx" http://localhost:8000/repos
```

**Any public user's repos:**
```bash
curl -H "Authorization: Bearer gho_xxxxxxxxxxxx" "http://localhost:8000/repos?username=torvalds"
```

**Sample JSON Response:**
```json
{
  "count": 3,
  "repositories": [
    {
      "id": 123456,
      "name": "my-project",
      "full_name": "yourusername/my-project",
      "description": "A sample project",
      "private": false,
      "html_url": "https://github.com/yourusername/my-project",
      "language": "Python",
      "stargazers_count": 5,
      "forks_count": 1,
      "updated_at": "2024-11-01T10:30:00Z"
    }
  ]
}
```

---

## All Endpoints

| Method | Endpoint | Type | Description |
|--------|----------|------|-------------|
| GET | `/login` | Redirect | Starts OAuth flow — redirects to GitHub |
| GET | `/callback?code=xxx` | Redirect | Exchanges code for token, redirects to webpage |
| GET | `/repos-page` | Webpage | Displays repositories in the browser UI |
| GET | `/repos` | JSON API | Returns repositories as JSON (requires Bearer token) |
| GET | `/repos?username=xxx` | JSON API | Returns any public user's repos as JSON |

---

## Token Storage

The access token is stored in the browser's `localStorage` under the key `github_access_token`. This means:

- You stay logged in even if you refresh the page
- Clicking **Logout** clears the token from localStorage
- To get a fresh token, visit `/login` again

---

## Error Responses

All API errors return JSON with an `"error"` key:

```json
{ "error": "Invalid or expired access token. Please re-authenticate." }
```

| Status | Meaning |
|--------|---------|
| 400 | Missing required parameter (e.g. no `code` in callback) |
| 401 | Missing, invalid, or expired access token |
| 403 | Token lacks required permissions |
| 404 | GitHub user or resource not found |
| 502 | GitHub API issue or unexpected response format |
