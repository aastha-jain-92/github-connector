"""
connector/views.py

HTTP layer only — views handle request parsing and response formatting.
All GitHub business logic is delegated to connector/services.py.

Endpoints:
    GET /login          → Redirect user to GitHub OAuth authorization page
    GET /callback       → Handle GitHub's redirect, exchange code for token
    GET /repos          → Fetch repositories (authenticated user or by username)
"""
from django.http import HttpResponse
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from django.template import loader
from rest_framework import status

from .services import GitHubOAuthService, GitHubRepoService
from .serializers import RepositorySerializer
from .exceptions import GitHubAuthenticationError, GitHubAPIError


# --------------------------------------------------------------------------- #
#  OAuth Views
# --------------------------------------------------------------------------- #

class GitHubLoginView(APIView):
    """
    Step 1 of the OAuth flow.

    Redirects the browser to GitHub's authorization page where the user
    can approve (or deny) access to their account.

    Method:  GET
    URL:     /login
    Auth:    None required
    """

    def get(self, request):
        authorization_url = GitHubOAuthService.get_authorization_url()
        return redirect(authorization_url)


class GitHubCallbackView(APIView):
    """
    Step 2 of the OAuth flow.

    GitHub redirects here after the user approves access, attaching a
    short-lived 'code' as a query parameter. We exchange that code for
    a real access token and return it to the client.

    Method:  GET
    URL:     /callback?code=<github_code>
    Auth:    None required (this IS the auth step)

    Response (200):
        {
            "message": "Authentication successful.",
            "access_token": "gho_xxxxxxxxxxxx",
            "usage_hint": "Pass this token as: Authorization: Bearer <token>"
        }
    """

    def get(self, request):
        code = request.query_params.get("code")

        if not code:
            return Response(
                {
                    "error": "Missing 'code' parameter.",
                    "detail": "GitHub should have included 'code' in the redirect URL. "
                              "Try the /login flow again.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            access_token = GitHubOAuthService.exchange_code_for_token(code)
        except GitHubAuthenticationError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Redirect to webpage with token instead of returning JSON
        return redirect(f"/repos-page?token={access_token}")

# --------------------------------------------------------------------------- #
#  Webpage View
# --------------------------------------------------------------------------- #

class ReposPageView(APIView):
    """
    Serves the repos HTML webpage.
    The page loads in the browser, reads the token from localStorage,
    then calls /repos API on its own to display repositories.

    Method:  GET
    URL:     /repos-page
    """

    def get(self, request):
        template = loader.get_template("repos.html")
        return HttpResponse(template.render({}, request))

# --------------------------------------------------------------------------- #
#  Repository View
# --------------------------------------------------------------------------- #

class UserRepositoriesView(APIView):
    """
    Fetch GitHub repositories, authenticated via Bearer token.

    - Without 'username' param  → returns the authenticated user's own repos
                                  (public + private, based on token scope)
    - With '?username=<name>'   → returns any public user's repos

    Method:  GET
    URL:     /repos
             /repos?username=torvalds

    Headers:
        Authorization: Bearer <access_token>

    Response (200):
        {
            "count": 42,
            "repositories": [ { ... }, ... ]
        }
    """

    def get(self, request):
        # ---- 1. Extract and validate the Bearer token ---- #
        access_token = self._extract_bearer_token(request)

        if not access_token:
            return Response(
                {
                    "error": "Authorization header missing or malformed.",
                    "detail": "Include the header: Authorization: Bearer <your_access_token>",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # ---- 2. Fetch repositories from GitHub ---- #
        username = request.query_params.get("username")
        repo_service = GitHubRepoService(access_token=access_token)

        try:
            if username:
                repositories = repo_service.fetch_repos_by_username(username)
            else:
                repositories = repo_service.fetch_authenticated_user_repos()

        except GitHubAPIError as exc:
            # Use GitHub's actual status code if available, else 502 Bad Gateway
            http_status = exc.status_code or status.HTTP_502_BAD_GATEWAY
            return Response({"error": exc.message}, status=http_status)

        # ---- 3. Serialize and return clean response ---- #
        serializer = RepositorySerializer(data=repositories, many=True)

        if not serializer.is_valid():
            return Response(
                {
                    "error": "Unexpected data format received from GitHub.",
                    "details": serializer.errors,
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                "count": len(serializer.validated_data),
                "repositories": serializer.validated_data,
            },
            status=status.HTTP_200_OK,
        )

    # ----------------------------------------------------------------------- #
    #  Private Helpers
    # ----------------------------------------------------------------------- #

    @staticmethod
    def _extract_bearer_token(request) -> str | None:
        """
        Safely parse the Bearer token from the Authorization request header.

        Expected format: "Authorization: Bearer gho_xxxxxxxxxxxxxxxx"

        Returns:
            str: The token string if found and well-formed.
            None: If the header is absent or does not follow Bearer format.
        """
        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split()

        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]

        return None
