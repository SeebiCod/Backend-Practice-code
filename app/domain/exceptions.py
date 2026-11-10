"""Errors raised by the inner layers. presentation/error_handlers.py maps them to HTTP codes."""


class EmailAlreadyRegisteredError(Exception):
    def __init__(self):
        super().__init__("An account with this email already exists")


class InvalidCredentialsError(Exception):
    """Same message for unknown email and wrong password, so emails can't be guessed."""

    def __init__(self):
        super().__init__("Invalid email or password")


class IncorrectCurrentPasswordError(Exception):
    def __init__(self):
        super().__init__("The current password is incorrect")


class PasswordUnchangedError(Exception):
    def __init__(self):
        super().__init__("The new password must be different from the current one")


class InvalidTokenError(Exception):
    """Missing, malformed, or expired token, or the user no longer exists."""


class PermissionDeniedError(Exception):
    pass
