"""Run: python tests/unit/cache.py (uses fakeredis, no external server)."""

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fakeredis.aioredis import FakeRedis
from redis.asyncio.client import Pipeline
from redis.exceptions import ResponseError

from src.backend.repository.cache import Cache


class CacheTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.redis = FakeRedis(decode_responses=True)
        self.cache = Cache(self.redis)

    async def asyncTearDown(self):
        await self.redis.aclose()

    async def test_operations(self):
        self.assertEqual(await self.cache.set("text", "hello"), {"set": True})
        self.assertEqual(await self.cache.get("text"), {"value": "hello"})
        self.assertEqual(await self.cache.hash("profile", {"name": "Test", "age": 18}), {"added": 2})
        self.assertEqual(await self.cache.hash("profile", {"age": 19}), {"added": 0})
        self.assertEqual(await self.cache.get("profile", hash=True), {"value": {"name": "Test", "age": "19"}})
        self.assertEqual(await self.cache.incr("counter"), {"value": 1})
        self.assertEqual(await self.cache.incr("counter", 4), {"value": 5})
        self.assertEqual(await self.cache.delete("text"), {"deleted": 1})
        self.assertEqual(await self.cache.delete("text"), {"deleted": 0})
        self.assertEqual(await self.cache.get("text"), {"value": None})
        self.assertEqual(await self.cache.get("absent", hash=True), {"value": {}})
        for key in ('profile', 'counter'):
            self.assertGreater(await self.redis.ttl(key), 0)
            self.assertLessEqual(await self.redis.ttl(key), 60)
        await self.cache.set('expiring', 'value')
        self.assertEqual(await self.redis.ttl('expiring'), 60)
        await self.redis.pexpire('expiring', 1)
        await asyncio.sleep(0.01)
        self.assertEqual(await self.cache.get('expiring'), {'value': None})

    async def test_watch_conflict_retries_every_operation(self):
        cases = [
            (lambda: self.cache.set("key", "new"), {"set": True}),
            (lambda: self.cache.hash("key", {"name": "Test"}), {"added": 1}),
            (lambda: self.cache.incr("key"), {"value": 1}),
            (lambda: self.cache.get("key"), {"value": None}),
            (lambda: self.cache.get("key", hash=True), {"value": {}}),
            (lambda: self.cache.delete("key"), {"deleted": 0}),
        ]
        original_execute = Pipeline.execute
        for index, (operation, expected) in enumerate(cases):
            with self.subTest(operation=index):
                await self.redis.delete("key")
                await self.redis.set("key", "0")
                attempts = []

                async def execute(pipeline, *args, **kwargs):
                    self.assertTrue(pipeline.watching)
                    self.assertTrue(pipeline.explicit_transaction)
                    attempts.append(pipeline)
                    if len(attempts) == 1:
                        # Modify the watched key after MULTI, before EXEC.
                        await self.redis.delete("key")
                    return await original_execute(pipeline, *args, **kwargs)

                with patch.object(Pipeline, "execute", execute):
                    self.assertEqual(await operation(), expected)
                self.assertEqual(len(attempts), 2)
                self.assertIsNot(attempts[0], attempts[1])
                self.assertTrue(all(pipeline.connection is None for pipeline in attempts))

    async def test_concurrent_increments(self):
        results = await asyncio.gather(*(self.cache.incr("counter") for _ in range(30)))
        self.assertEqual(sorted(result["value"] for result in results), list(range(1, 31)))
        self.assertEqual(await self.cache.get("counter"), {"value": "30"})

    async def test_invalid_data_and_non_watch_errors_propagate(self):
        with self.assertRaises(TypeError):
            Cache(None)
        with self.assertRaises(ValueError):
            await self.cache.get("")
        with self.assertRaises(ValueError):
            await self.cache.hash("key", {})
        with self.assertRaises(TypeError):
            await self.cache.incr("key", True)
        await self.cache.set("key", "text")
        with self.assertRaises(ResponseError):
            await self.cache.incr("key")
        self.assertEqual(await self.cache.get("key"), {"value": "text"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
