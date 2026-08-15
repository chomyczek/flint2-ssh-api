class SSHResponse:
    def __init__(self, success: bool, response: str):
        self.success = success
        self.response = response

    def __str__(self):
        return str(self.response)