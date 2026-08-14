from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "FLINT2 SSH API"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # SSH
    router_host: str
    router_ssh_port: int
    router_ssh_username: str
    router_ssh_password: str
    ssh_command_timeout: int = 5
    ssh_keepalive_interval: int = 5
settings = Settings()
