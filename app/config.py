from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "FLINT2 SSH API"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # SSH
    router_host: str = "192.168.8.1"
    router_ssh_port: int = 22
    router_ssh_username: str = "root"
    router_ssh_password: str = "your_password_here"
    ssh_command_timeout: int = 5
    ssh_keepalive_interval: int = 5


settings = Settings()
