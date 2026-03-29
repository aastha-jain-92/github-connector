from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------ #
#  SECURITY
# ------------------------------------------------------------------ #
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = ["*"]

# ------------------------------------------------------------------ #
#  APPLICATIONS
# ------------------------------------------------------------------ #
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "connector"
]

# ── Templates ── #
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,   # auto-discovers templates/ inside each app
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]
# ------------------------------------------------------------------ #
#  MIDDLEWARE
# ------------------------------------------------------------------ #
MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

# ------------------------------------------------------------------ #
#  URLS & WSGI
# ------------------------------------------------------------------ #
ROOT_URLCONF = "github_connector.urls"
WSGI_APPLICATION = "github_connector.wsgi.application"

# ------------------------------------------------------------------ #
#  DATABASE
# ------------------------------------------------------------------ #
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ------------------------------------------------------------------ #
#  DJANGO REST FRAMEWORK
# ------------------------------------------------------------------ #
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

# ------------------------------------------------------------------ #
#  GITHUB OAUTH CONFIGURATION  (all values loaded from .env)
# ------------------------------------------------------------------ #
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github/callback/")

# GitHub endpoints
GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
