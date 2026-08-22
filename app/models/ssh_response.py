from dataclasses import dataclass


@dataclass
class SSHResponse:
    success: bool
    output: str
    exit_code: int

    def __str__(self):
        return str(self.output)
