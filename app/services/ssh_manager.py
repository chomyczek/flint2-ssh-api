import asyncio
import logging

import asyncssh

from app.config import settings


class SSHManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._connection: asyncssh.SSHClientConnection | None = None
        self._lock = asyncio.Lock()
        self.reconnect_count = 0

    async def connect(self):
        self.logger.info(f"Connecting to router at {settings.router_host}..")
        try:
            self._connection = await asyncssh.connect(host=settings.router_host, port=settings.router_ssh_port,
                                                      username=settings.router_ssh_username,
                                                      password=settings.router_ssh_password,
                                                      keepalive_interval=settings.ssh_keepalive_interval)
        except TimeoutError:
            self.logger.error("Failed to connect to router")
            return
        self.logger.info("SSH connection established")

    async def run_command(self, command: str) -> str:
        async with self._lock:
            if await self._ensure_connected():
                result = await asyncio.wait_for(self._connection.run(command), timeout=settings.ssh_command_timeout)
                return result.stdout.strip()
            return ""

    def is_connected(self) -> bool:
        return self._connection is not None and not self._connection.is_closed()

    async def _ensure_connected(self):
        if not self.is_connected():
            self.logger.warning("SSH connection lost, reconnecting..")
            self.reconnect_count += 1
            await self.connect()
            return self.is_connected()
        return True

    async def disconnect(self):
        if self._connection:
            self._connection.close()
            await self._connection.wait_closed()
            self._connection = None
            self.logger.info("SSH connection closed")


ssh_manager = SSHManager()
