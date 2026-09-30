"""Async Redis cache operations with optimistic transactions and retries."""

import asyncio
from collections.abc import Callable
from typing import Any

from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from redis.exceptions import WatchError

from src.backend.logs.log import logger, log_operation


class Cache:
    @log_operation
    def __init__(self, redis: Redis, ttl: int = 60) -> None:
        if not isinstance(redis, Redis):
            raise TypeError("Cache requires an async Redis client")
        self.redis = redis
        if isinstance(ttl, bool) or not isinstance(ttl, int) or ttl <= 0:
            raise ValueError("Cache TTL must be a positive integer")
        self.ttl = ttl

    @log_operation
    async def _execute(self, key: str, command: Callable[[Pipeline], Any]) -> Any:
        if not isinstance(key, str) or not key:
            raise ValueError("Provide a non-empty cache key")
        while True:
            try:
                async with self.redis.pipeline(transaction=True) as pipeline:
                    await pipeline.watch(key)
                    pipeline.multi()
                    command(pipeline)
                    return (await pipeline.execute())[0]
            except WatchError:
                logger.warning("Conflito na transação do cache; repetindo operação")
                await asyncio.sleep(0)

    @log_operation
    async def hash(self, key: str, data: dict[str, str | int | float]) -> dict[str, int]:
        if not isinstance(data, dict) or not data:
            raise ValueError("Provide a non-empty hash mapping")
        added = await self._execute(key, lambda pipeline: pipeline.hset(key, mapping=data).expire(key, self.ttl))
        return {"added": added}

    @log_operation
    async def set(
        self,
        key: str,
        value: str | int | float,
        expire: int | None = None,
    ) -> dict[str, bool]:
        ttl = self.ttl if expire is None else expire
        if isinstance(ttl, bool) or not isinstance(ttl, int) or ttl <= 0:
            raise ValueError("Expire time must be a positive integer")
        result = await self._execute(
            key,
            lambda pipeline: pipeline.set(key, value, ex=ttl),
        )
        return {"set": bool(result)}

    @log_operation
    async def consume(self, key: str, expected: str) -> dict[str, bool]:
        if not isinstance(key, str) or not key:
            raise ValueError("Provide a non-empty cache key")
        if not isinstance(expected, str) or not expected:
            raise ValueError("Provide the expected cache value")

        while True:
            try:
                async with self.redis.pipeline(transaction=True) as pipeline:
                    await pipeline.watch(key)
                    current = await pipeline.get(key)

                    if current is None:
                        return {"consumed": False, "found": False}

                    current_value = (
                        current.decode()
                        if isinstance(current, bytes)
                        else str(current)
                    )

                    if current_value != expected:
                        return {"consumed": False, "found": True}

                    pipeline.multi()
                    pipeline.delete(key)
                    deleted = (await pipeline.execute())[0]
                    return {
                        "consumed": bool(deleted),
                        "found": True,
                    }
            except WatchError:
                logger.warning(
                    "Conflito ao consumir valor do cache; repetindo operação"
                )
                await asyncio.sleep(0)

    @log_operation
    async def incr(self, key: str, amount: int = 1) -> dict[str, int]:
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError("Increment amount must be an integer")
        value = await self._execute(key, lambda pipeline: pipeline.incrby(key, amount).expire(key, self.ttl))
        return {"value": value}

    @log_operation
    async def get(self, key: str, hash: bool = False) -> dict[str, Any]:
        value = await self._execute(
            key, lambda pipeline: pipeline.hgetall(key) if hash else pipeline.get(key),
        )
        return {"value": value}

    @log_operation
    async def delete(self, key: str) -> dict[str, int]:
        deleted = await self._execute(key, lambda pipeline: pipeline.delete(key))
        return {"deleted": deleted}
