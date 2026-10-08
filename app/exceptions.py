class RouterUnavailableError(Exception):
    """Raised when the router is unavailable or cannot be reached over SSH."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class SSHCommandError(Exception):
    """Raised when an SSH command returns an unexpected error."""

    def __init__(self, command: str, detail: str) -> None:
        super().__init__(detail)
        self.command = command
        self.detail = detail
