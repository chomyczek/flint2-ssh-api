class SSHResponse:
    def __init__(self, success: bool, output: str):
        self.success = success
        self.output = output

    def __str__(self):
        return str(self.output)
