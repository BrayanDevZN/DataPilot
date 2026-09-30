"""Compose committed SQL operations and Redis cache lookups."""

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from datetime import datetime
from typing import Any
from uuid import UUID

from redis.asyncio import Redis
from redis.asyncio.lock import Lock
from redis.exceptions import LockNotOwnedError
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.logs.log import logger, log_operation
from ..cache import Cache
from ..db.base import Base
from ..db.control_base import TableControl


class CachedControl:
    controller: type[TableControl]

    @log_operation
    def __init__(self, redis: Redis, session: AsyncSession) -> None:
        self.cache = Cache(redis)
        self.db = self.controller(session)
        self.session = session
        self.table = self.db.table
        self.identifiers = [self.db.primary_key.name]
        if 'public_id' in self.table.c:
            self.identifiers.append('public_id')
        if self.table.name == 'users':
            self.identifiers.extend(['email', 'username'])

    @log_operation
    async def _renew_lock(self, lock: Lock, owner: asyncio.Task) -> None:
        try:
            while True:
                await asyncio.sleep(20)
                await lock.extend(60, replace_ttl=True)
        except Exception as error:
            logger.error('Falha ao renovar coordenação do cache (%s)', type(error).__name__)
            owner.cancel()

    @asynccontextmanager
    async def _lock(self) -> AsyncIterator[Lock]:
        async with self.cache.redis.lock('_repository:control:lock', timeout=60, blocking_timeout=10) as lock:
            logger.info('Coordenação de banco e cache adquirida')
            renewal = asyncio.create_task(self._renew_lock(lock, asyncio.current_task()))
            try:
                yield lock
            finally:
                renewal.cancel()
                with suppress(asyncio.CancelledError):
                    await renewal
                logger.info('Encerrando coordenação de banco e cache')

    @log_operation
    def _lookup(self, identifier: str, value: Any) -> tuple[str, Any]:
        if identifier not in self.identifiers:
            raise ValueError('Select using a unique identifier of this table')
        column = self.table.c[identifier]
        if column.type.python_type is UUID:
            value = UUID(str(value))
        elif column.type.python_type is int:
            if isinstance(value, bool):
                raise ValueError('Identifier must be an integer')
            value = int(value)
        else:
            value = str(value).strip().lower()
        return f'{self.table.name}:{identifier}:{value}', value

    @log_operation
    def _ready(self) -> None:
        if self.session.in_transaction():
            raise ValueError('Finish the current session transaction before using cached controls')

    @log_operation
    async def _store(self, row: dict[str, Any]) -> None:
        payload = json.dumps(row, default=str, ensure_ascii=False)
        for identifier in self.identifiers:
            key, _ = self._lookup(identifier, row[identifier])
            await self.cache.set(key, payload)

    @log_operation
    def _decode(self, payload: str | bytes) -> dict[str, Any]:
        row = json.loads(payload)
        for column in self.table.c:
            value = row.get(column.name)
            if value is not None and column.type.python_type in (UUID, datetime):
                row[column.name] = UUID(value) if column.type.python_type is UUID else datetime.fromisoformat(value)
        return row

    @log_operation
    async def _invalidate(self, *, cascade: bool = False) -> None:
        tables = Base.metadata.tables if cascade else [self.table.name]
        for table in tables:
            async for key in self.cache.redis.scan_iter(match=f'{table}:*'):
                await self.cache.delete(key.decode() if isinstance(key, bytes) else key)

    @log_operation
    async def insert(self, data: dict[str, Any]) -> dict[str, Any]:
        self._ready()
        async with self._lock() as lock:
            row = (await self.db.create(data))['item']
            if not await lock.owned():
                raise LockNotOwnedError('Cache coordination lock expired')
            await self._store(row)
            return row

    @log_operation
    async def select(self, identifier: str, value: Any) -> dict[str, Any] | None:
        self._ready()
        key, value = self._lookup(identifier, value)
        async with self._lock() as lock:
            payload = (await self.cache.get(key))['value']
            if payload is not None:
                logger.info('Registro encontrado no cache de %s', self.table.name)
                return self._decode(payload)
            rows = await self.db.list(filters={identifier: value}, limit=1)
            if not rows['items']:
                return None
            row = rows['items'][0]
            if not await lock.owned():
                raise LockNotOwnedError('Cache coordination lock expired')
            await self._store(row)
            return row

    @log_operation
    async def update(self, identifier: str, value: Any, data: dict[str, Any]) -> dict[str, Any] | None:
        self._ready()
        _, value = self._lookup(identifier, value)
        async with self._lock():
            # Invalidate before and after the commit; aliases cannot keep old values.
            await self._invalidate()
            async with self.session.begin():
                rows = await self.db.list(filters={identifier: value}, limit=1)
                if not rows['items']:
                    return None
                row = rows['items'][0]
                result = await self.db.update(row[self.db.primary_key.name], data)
            await self._invalidate()
            return result['item']

    @log_operation
    async def delete(self, identifier: str, value: Any) -> dict[str, Any]:
        self._ready()
        _, value = self._lookup(identifier, value)
        async with self._lock():
            # FK cascades and SET NULL can affect records cached by other controls.
            await self._invalidate(cascade=True)
            async with self.session.begin():
                rows = await self.db.list(filters={identifier: value}, limit=1)
                if not rows['items']:
                    return {'deleted': False, 'id': None}
                result = await self.db.delete(rows['items'][0][self.db.primary_key.name])
            await self._invalidate(cascade=True)
            return result
