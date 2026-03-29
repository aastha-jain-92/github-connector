"""
connector/exceptions.py

Custom exception classes for the GitHub connector.
Using typed exceptions makes error handling explicit and readable
throughout the codebase — no ambiguous bare Exception catches.
"""


class GitHubAuthenticationError(Exception):
    """
    Raised when GitHub OAuth authentication fails.
    Examples: bad client secret, expired code, token exchange failure.
    """
    pass


class GitHubAPIError(Exception):
    """
    Raised when a GitHub REST API call returns a non-success response.
    Carries an optional HTTP status_code for the view layer to forward.
    """

    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class MissingParameterError(Exception):
    """
    Raised when a required query parameter or input is absent.
    """
    pass
