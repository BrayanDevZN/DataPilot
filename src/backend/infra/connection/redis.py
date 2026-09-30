"""Async Redis connection; data operations belong in repositories."""

from redis.asyncio import Redis

from src.backend.logs.log import logger, log_operation


class RedisConnection:
    @log_operation
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0) -> None:
        self._host = host
        self._port = port
        self._db = db
        self._client: Redis | None = None

    @log_operation
    def create_client(self) -> Redis:
        if self._client is None:
            self._client = Redis(
                host=self._host, port=self._port, db=self._db,
                decode_responses=True, socket_connect_timeout=5, socket_timeout=5,
            )
        logger.info("Cliente Redis assíncrono disponível")
        return self._client

    @property
    @log_operation
    def client(self) -> Redis:
        return self.create_client()

    @log_operation
    async def test(self) -> bool:
        return await self.create_client().ping()

    @log_operation
    async def test_connection(self) -> bool:
        return await self.test()

    @log_operation
    async def __call__(self) -> Redis:
        client = self.create_client()
        try:
            if not await self.test():
                raise ConnectionError("Redis connection test failed")
        except Exception:
            await self.close()
            raise
        return client

    @log_operation
    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
