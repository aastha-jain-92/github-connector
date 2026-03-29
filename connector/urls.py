"""
connector/urls.py

URL routing for the GitHub connector app.

    /               → Login landing page
    /login          → Start OAuth flow (redirects to GitHub)
    /callback       → GitHub redirects here after user approves
    /dashboard      → Visual repos page (reads token from ?token=)
    /repos          → JSON API endpoint
"""

from django.urls import path
from .views import (
    # HomePageView,
    # DashboardPageView,
    GitHubLoginView,
    GitHubCallbackView,
    UserRepositoriesView,
    ReposPageView
)

urlpatterns = [
    # path("",            HomePageView.as_view(),       name="home"),
    path("login",       GitHubLoginView.as_view(),    name="github-login"),
    path("auth/github/callback/",    GitHubCallbackView.as_view(), name="github-callback"),
    # path("dashboard",   DashboardPageView.as_view(),  name="dashboard"),
    path("repos",       UserRepositoriesView.as_view(),name="user-repositories"),
    path("repos-page", ReposPageView.as_view(), name="repos-page"),
]


