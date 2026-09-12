from dataclasses import dataclass


@dataclass
class SSHResponse:
    """Result of a command executed over an SSH connection."""

    success: bool
    output: str
    exit_code: int

    def __str__(self) -> str:
        """Return the command output as string.

        Returns: Command standard output.
        """
        return str(self.output)
