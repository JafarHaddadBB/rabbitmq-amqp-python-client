# For the moment this is just a Connection pooler to keep compatibility with other clients
import logging
from typing import Annotated, Callable, Optional, TypeVar

from .connection import Connection
from .ssl_configuration import SslConfigurationContext

logger = logging.getLogger(__name__)

MT = TypeVar("MT")
CB = Annotated[Callable[[MT], None], "Message callback type"]

import asyncio

class Environment:
    """
    Environment class for managing AMQP connections.

    This class serves as a connection pooler to maintain compatibility with other clients.
    It manages a collection of connections and provides methods for creating and managing
    these connections.

    Attributes:
        _connections (list[Connection]): List of active connections managed by this environment
    """

    def __init__(self):  # type: ignore
        """
        Initialize a new Environment instance.

        Creates an empty list to track active connections.
        """
        self._connections: list[Connection] = []

    async def connection(
        self,
        # single-node mode
        uri: Optional[str] = None,
        # multi-node mode
        uris: Optional[list[str]] = None,
        ssl_context: Optional[SslConfigurationContext] = None,
        on_disconnection_handler: Optional[CB] = None,  # type: ignore
    ) -> Connection:
        """
        Create and return a new connection.

        This method supports both single-node and multi-node configurations, with optional
        SSL/TLS security and disconnection handling.

        Args:
            uri: Single node connection URI
            uris: List of URIs for multi-node setup
            ssl_context: SSL configuration for secure connections
            on_disconnection_handler: Callback for handling disconnection events

        Returns:
            Connection: A new connection instance

        Raises:
            ValueError: If neither uri nor uris is provided
        """
        connection = Connection(
            uri=uri,
            uris=uris,
            ssl_context=ssl_context,
            on_disconnection_handler=on_disconnection_handler,
        )
        logger.debug("Environment: Creating and returning a new connection")
        self._connections.append(connection)
        await connection._set_environment_connection_list(self._connections)
        return connection

    # closes all active connections
    async def close(self) -> None:
        """
        Close all active connections.

        Iterates through all connections managed by this environment and closes them.
        This method should be called when shutting down the application to ensure
        proper cleanup of resources.
        """
        errors = []
        for connection in self._connections:
            try:
                await connection.close()
            except Exception as e:
                errors.append(f"Exception closing connection: {str(e)}")
                logger.error(f"Exception closing connection: {e}")

        if errors:
            raise RuntimeError(f"Errors closing connections: {'; '.join(errors)}")

    async def connections(self) -> list[Connection]:
        """
        Get the list of active connections.

        Returns:
            list[Connection]: List of all active connections managed by this environment
        """
        return self._connections

    def __enter__(self) -> "Environment":
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        """Close all connections when the context terminate."""
        self.close()

    @property
    async def active_connections(self) -> int:
        """Returns the number of active connections"""
        return len(self._connections)
