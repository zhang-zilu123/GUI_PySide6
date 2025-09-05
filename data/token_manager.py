class TokenManager:
    """Manages authentication tokens for users."""

    def __init__(self):
        self.token = ""

    def set_token(self, token):
        """Sets the authentication token."""
        self.token = token

token_manager = TokenManager()
