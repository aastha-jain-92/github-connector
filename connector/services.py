"""
connector/services.py

All GitHub business logic lives here — completely decoupled from HTTP views.
This keeps views thin (handle request/response only) and services testable
and reusable independently.

Classes:
    GitHubOAuthService  — OAuth 2.0 flow: build auth URL, exchange code for token
    GitHubRepoService   — GitHub API calls: fetch repos for user or authenticated account
"""

import requests
from django.conf import settings

from .exceptions import GitHubAuthenticationError, GitHubAPIError


# --------------------------------------------------------------------------- #
#  OAuth Service
# --------------------------------------------------------------------------- #

class GitHubOAuthService:
    """
    Handles the two-step GitHub OAuth 2.0 authentication flow.

    Step 1 — get_authorization_url()
        Build the URL that sends the user to GitHub's permission screen.

    Step 2 — exchange_code_for_token(code)
        After GitHub redirects back with a 'code', exchange it for a real token.
    """

    @staticmethod
    def get_authorization_url() -> str:
        """
        Build the GitHub OAuth authorization URL.

        The user is redirected here so they can approve access.
        'scope' determines what permissions we request:
            - read:user  → read basic profile info
            - repo       → read public and private repositories

        Returns:
            str: Full GitHub authorization URL with query parameters.
        """
        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
            "scope": "read:user repo",
        }
        query_string = "&".join(f"{key}={value}" for key, value in params.items())
        return f"{settings.GITHUB_OAUTH_AUTHORIZE_URL}?{query_string}"

    @staticmethod
    def exchange_code_for_token(code: str) -> str:
        """
        Exchange the temporary OAuth authorization code for a long-lived access token.

        GitHub sends a short-lived 'code' to our callback URL after user approval.
        We POST that code (along with our app credentials) to GitHub's token endpoint
        to receive the actual access token.

        Args:
            code (str): Temporary code from GitHub's callback redirect.

        Returns:
            str: GitHub OAuth access token.

        Raises:
            GitHubAuthenticationError: If the exchange fails for any reason.
        """
        payload = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
        }
        headers = {"Accept": "application/json"}

        try:
            response = requests.post(
                settings.GITHUB_OAUTH_TOKEN_URL,
                json=payload,
                headers=headers,
                timeout=10,
            )
        except requests.exceptions.ConnectionError:
            raise GitHubAuthenticationError(
                "Cannot connect to GitHub. Check your internet connection."
            )
        except requests.exceptions.Timeout:
            raise GitHubAuthenticationError(
                "GitHub token endpoint timed out. Try again."
            )

        if response.status_code != 200:
            raise GitHubAuthenticationError(
                f"Token exchange failed. GitHub responded with HTTP {response.status_code}."
            )

        data = response.json()

        # GitHub can return HTTP 200 but include an 'error' key in the body
        if "error" in data:
            error_description = data.get("error_description", data["error"])
            raise GitHubAuthenticationError(
                f"GitHub OAuth error: {error_description}"
            )

        access_token = data.get("access_token")
        if not access_token:
            raise GitHubAuthenticationError(
                "GitHub did not return an access token. Please try logging in again."
            )

        return access_token


# --------------------------------------------------------------------------- #
#  Repository Service
# --------------------------------------------------------------------------- #

class GitHubRepoService:
    """
    Fetches repository data from the GitHub REST API.

    Requires a valid OAuth access token passed at construction time.
    All requests are authenticated via the Authorization: Bearer header.

    Usage:
        service = GitHubRepoService(access_token="gho_xxx")
        repos = service.fetch_authenticated_user_repos()
    """

    def __init__(self, access_token: str):
        self.base_url = settings.GITHUB_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _make_get_request(self, endpoint: str) -> list | dict:
        """
        Internal helper: perform a GET request to the GitHub API.

        Centralises all HTTP logic, timeout handling, and status-code checking
        so individual public methods stay clean and focused.

        Args:
            endpoint (str): API path relative to base URL, e.g. '/user/repos'.

        Returns:
            list | dict: Parsed JSON from GitHub.

        Raises:
            GitHubAPIError: For any non-200 response or connectivity issue.
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
        except requests.exceptions.ConnectionError:
            raise GitHubAPIError(
                "Unable to reach GitHub API. Check your internet connection."
            )
        except requests.exceptions.Timeout:
            raise GitHubAPIError(
                "GitHub API request timed out. Please try again."
            )

        # Map common status codes to meaningful error messages
        error_map = {
            401: "Invalid or expired access token. Please re-authenticate.",
            403: "Access forbidden. Your token may lack the required permissions.",
            404: "The requested GitHub resource was not found.",
            422: "Invalid input sent to GitHub API.",
            500: "GitHub API is experiencing issues. Try again later.",
        }

        if response.status_code in error_map:
            raise GitHubAPIError(
                error_map[response.status_code],
                status_code=response.status_code,
            )

        if response.status_code != 200:
            raise GitHubAPIError(
                f"Unexpected response from GitHub API (HTTP {response.status_code}).",
                status_code=response.status_code,
            )

        return response.json()

    def fetch_authenticated_user_repos(self) -> list:
        """
        Fetch all repositories belonging to the currently authenticated user.

        Returns repositories sorted by last-updated, up to 100 per call.
        Includes both public and private repos the token has access to.

        Returns:
            list: List of repository objects from GitHub.
        """
        return self._make_get_request("/user/repos?sort=updated&per_page=100")

    def fetch_repos_by_username(self, username: str) -> list:
        """
        Fetch public repositories for any GitHub user by their username.

        Args:
            username (str): GitHub username to look up (e.g. 'torvalds').

        Returns:
            list: List of public repository objects for that user.
        """
        return self._make_get_request(
            f"/users/{username}/repos?sort=updated&per_page=100"
        )
