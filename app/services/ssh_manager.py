import asyncio
import logging

import asyncssh
from asyncssh import HostKeyNotVerifiable, PermissionDenied, Error

from app.config import settings
from app.exceptions import SSHCommandError, RouterUnavailableError
from app.models.ssh_response import SSHResponse

logger = logging.getLogger(__name__)


class SSHManager:
    """Manage a persistent SSH connection to the router.

    Raises:
        RouterUnavailableError: When connection cannot be established."""

    def __init__(self) -> None:
        self._connection: asyncssh.SSHClientConnection | None = None
        self._lock = asyncio.Lock()
        self.reconnect_count = 0

    async def connect(self) -> None:
        """Establish an SSH connection to the router."""
        logger.info(f"Connecting to router at {settings.router_host}..")
        try:
            self._connection = await asyncssh.connect(
                host=settings.router_host,
                port=settings.router_ssh_port,
                username=settings.router_ssh_username,
                password=settings.router_ssh_password,
                keepalive_interval=settings.ssh_keepalive_interval,
            )
        except TimeoutError as e:
            logger.error(f"SSH connection timed out: {e}")
            raise RouterUnavailableError("Connection timed out") from e
        except HostKeyNotVerifiable as e:
            logger.error(f"SSH host key not verifiable: {e}")
            raise RouterUnavailableError("Host key not verifiable") from e
        except PermissionDenied as e:
            logger.error(f"SSH permission denied: {e}")
            raise RouterUnavailableError("Permission denied") from e
        except Error as e:
            logger.error(f"SSH error during connect: {e}")
            raise RouterUnavailableError(f"SSH error: {e}") from e
        except (TimeoutError, HostKeyNotVerifiable) as e:
            logger.error("Failed to connect to router")
            logger.debug(f"Exception: {e}")
            return
        logger.info("SSH connection established")

    async def run_command(self, command: str) -> SSHResponse:
        """Run a command on the router through SSH.

        Args:
            command: Shell command to execute.

        Returns: Result of the command.

        Raises:
            RouterUnavailableError: When connection cannot be reached.
            SSHCommandError: When command execution fails unexpectedly.
        """
        async with self._lock:
            await self._ensure_connected()

            try:
                result = await asyncio.wait_for(self._connection.run(command), timeout=settings.ssh_command_timeout)
            except TimeoutError as e:
                logger.error(f"SSH command timed out: {command!r}")
                raise SSHCommandError(command, f"Command timed out") from e
            except Error as e:
                logger.error(f"SSH error during command: {command!r}: {e}")
                raise SSHCommandError(command, f"SSH error: {e}") from e

            exit_status = result.exit_status if result.exit_status is not None else -1
            return SSHResponse(str(result.stdout).strip(), exit_status)

    def is_connected(self) -> bool:
        """Check whether an active SSH connection exists.

        Returns: True when SSH connection is active, False otherwise.
        """
        return self._connection is not None and not self._connection.is_closed()

    async def _ensure_connected(self) -> bool:
        if not self.is_connected():
            logger.warning("SSH connection lost, reconnecting..")
            self.reconnect_count += 1
            await self.connect()
            return self.is_connected()
        return True

    async def disconnect(self) -> None:
        """Close the Active SSH connection, if exists."""
        if self._connection:
            self._connection.close()
            await self._connection.wait_closed()
            self._connection = None
            logger.info("SSH connection closed")


ssh_manager = SSHManager()
