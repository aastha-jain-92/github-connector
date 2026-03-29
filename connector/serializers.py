"""
connector/serializers.py

DRF serializers for shaping API responses.

Rather than forwarding raw GitHub API responses (which contain 80+ fields),
we explicitly declare only the fields we want to expose. This keeps our
API contract clean, predictable, and independent of GitHub's data shape.
"""

from rest_framework import serializers


class RepositorySerializer(serializers.Serializer):
    """
    Serializes a single GitHub repository object.

    Fields selected for developer relevance and clarity.
    Nullable fields (description, language) are marked allow_null=True
    since GitHub legitimately returns null for repos without them.
    """

    id = serializers.IntegerField(
        help_text="GitHub's internal unique identifier for the repository."
    )
    name = serializers.CharField(
        help_text="Short repository name, e.g. 'django'."
    )
    full_name = serializers.CharField(
        help_text="Owner/repo format, e.g. 'django/django'."
    )
    description = serializers.CharField(
        allow_null=True,
        help_text="Optional human-readable description of the repository."
    )
    private = serializers.BooleanField(
        help_text="True if the repository is private."
    )
    html_url = serializers.URLField(
        help_text="Direct URL to the repository on GitHub.com."
    )
    language = serializers.CharField(
        allow_null=True,
        help_text="Primary programming language detected by GitHub."
    )
    stargazers_count = serializers.IntegerField(
        help_text="Number of users who have starred this repository."
    )
    forks_count = serializers.IntegerField(
        help_text="Number of forks created from this repository."
    )
    updated_at = serializers.DateTimeField(
        help_text="ISO 8601 timestamp of the last push or metadata update."
    )
