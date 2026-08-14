import asyncio
import logging

import asyncssh

from app.config import settings


class SSHManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._connection: asyncssh.SSHClientConnection | None = None
        self._lock = asyncio.Lock()

    async def connect(self):
        self.logger.info(f"Connecting to router at {settings.router_host}..")
        self._connection = await asyncssh.connect(host=settings.router_host, port=settings.router_ssh_port,
                                                  username=settings.router_ssh_username, password=settings.router_ssh_password,
                                                  keepalive_interval=settings.ssh_keepalive_interval)
        self.logger.info("SSH connection established")

    async def run_command(self, command: str) -> str:
        async with self._lock:
            result = await asyncio.wait_for(self._connection.run(command), timeout=settings.ssh_command_timeout)
            return result.stdout.strip()
