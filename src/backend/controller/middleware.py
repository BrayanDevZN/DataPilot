"""HTTP middleware for global and per-client rate limiting."""

from hashlib import sha256
from time import time
from typing import Iterable

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.backend.domain.module import InvalidTokenError
from src.backend.logs.log import logger
from src.backend.service.manage import jwt, redis


class Middleware(BaseHTTPMiddleware):
    """Apply global and client-scoped rate limits to every HTTP request."""

    def __init__(
        self,
        app,
        *,
        global_limit: int = 10_000,
        rate_limit: int = 120,
        window_seconds: int = 60,
        public_routes: Iterable[str] | None = None,
        trust_proxy_headers: bool = False,
    ) -> None:
        super().__init__(app)

        if global_limit <= 0:
            raise ValueError("global_limit must be positive")
        if rate_limit <= 0:
            raise ValueError("rate_limit must be positive")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

        self.default_global_limit = global_limit
        self.default_rate_limit = rate_limit
        self.window_seconds = window_seconds
        self.public_routes = {
            self._normalize_path(path)
            for path in (public_routes or ())
        }
        self.trust_proxy_headers = trust_proxy_headers

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        global_limit, rate_limit = await self._load_limits()

        global_count = await self._increment(
            self._global_key(),
        )

        if global_count > global_limit:
            logger.warning("Rate limit global excedido")
            return self._too_many_requests(
                limit=global_limit,
                scope="global",
            )

        is_public = self._is_public_route(request)

        if is_public:
            identity = f"ip:{self._client_ip(request)}"
        else:
            identity = self._private_identity(request)

        client_count = await self._increment(
            self._client_key(identity),
        )

        if client_count > rate_limit:
            logger.warning(
                "Rate limit excedido para escopo %s",
                "public" if is_public else "private",
            )
            return self._too_many_requests(
                limit=rate_limit,
                scope="public" if is_public else "private",
            )

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, rate_limit - client_count)
        )
        response.headers["X-RateLimit-Reset"] = str(
            self._seconds_until_reset()
        )

        return response

    def _is_public_route(self, request: Request) -> bool:
        """Return whether the current path is configured as public."""
        return self._normalize_path(request.url.path) in self.public_routes

    def _private_identity(self, request: Request) -> str:
        """Prefer a validated JWT user identity for private routes."""
        token = request.cookies.get("access_token")

        if not token:
            authorization = request.headers.get("authorization", "")
            scheme, _, bearer = authorization.partition(" ")
            if scheme.lower() == "bearer" and bearer.strip():
                token = bearer.strip()

        if token:
            try:
                claims = jwt.read(token)
            except InvalidTokenError:
                return f"token:{self._token_fingerprint(token)}"

            if claims.get("token_type") == "access":
                for claim in ("public_id", "user_id", "sub"):
                    value = claims.get(claim)
                    if value is not None:
                        return str(value)

            return f"token:{self._token_fingerprint(token)}"

        return f"ip:{self._client_ip(request)}"

    def _client_ip(self, request: Request) -> str:
        """Resolve the client IP, respecting common reverse-proxy headers."""
        if self.trust_proxy_headers:
            forwarded = request.headers.get("x-forwarded-for")

            if forwarded:
                return forwarded.split(",", 1)[0].strip()

            real_ip = request.headers.get("x-real-ip")
            if real_ip:
                return real_ip.strip()

        if request.client:
            return request.client.host

        return "unknown"

    async def _load_limits(self) -> tuple[int, int]:
        """Initialize rate-limit configuration in Redis and read it back."""
        global_key = "rate_limit:config:global_limit"
        client_key = "rate_limit:config:client_limit"

        async with redis.pipeline(transaction=True) as pipeline:
            pipeline.setnx(global_key, self.default_global_limit)
            pipeline.setnx(client_key, self.default_rate_limit)
            pipeline.mget(global_key, client_key)
            result = await pipeline.execute()

        raw_global, raw_client = result[2]

        try:
            global_limit = int(raw_global)
            rate_limit = int(raw_client)
        except (TypeError, ValueError):
            logger.error("Configuração de rate limit inválida no Redis")
            await self.set_limits(
                global_limit=self.default_global_limit,
                rate_limit=self.default_rate_limit,
            )
            return self.default_global_limit, self.default_rate_limit

        if global_limit <= 0 or rate_limit <= 0:
            logger.error("Rate limit não positivo encontrado no Redis")
            await self.set_limits(
                global_limit=self.default_global_limit,
                rate_limit=self.default_rate_limit,
            )
            return self.default_global_limit, self.default_rate_limit

        return global_limit, rate_limit

    async def set_limits(
        self,
        *,
        global_limit: int | None = None,
        rate_limit: int | None = None,
    ) -> None:
        """Persist rate-limit configuration in Redis."""
        if global_limit is not None and global_limit <= 0:
            raise ValueError("global_limit must be positive")
        if rate_limit is not None and rate_limit <= 0:
            raise ValueError("rate_limit must be positive")

        mapping: dict[str, int] = {}

        if global_limit is not None:
            mapping["rate_limit:config:global_limit"] = global_limit

        if rate_limit is not None:
            mapping["rate_limit:config:client_limit"] = rate_limit

        if not mapping:
            return

        async with redis.pipeline(transaction=True) as pipeline:
            for key, value in mapping.items():
                pipeline.set(key, value)
            await pipeline.execute()

    def _global_key(self) -> str:
        return f"rate_limit:global:{self._window_id()}"

    def _client_key(self, identity: str) -> str:
        return f"rate_limit:{identity}"

    def _window_id(self) -> int:
        return int(time() // self.window_seconds)

    def _seconds_until_reset(self) -> int:
        elapsed = int(time()) % self.window_seconds
        return self.window_seconds - elapsed

    async def _increment(self, key: str) -> int:
        """Atomically increment a fixed-window Redis counter."""
        async with redis.pipeline(transaction=True) as pipeline:
            pipeline.incr(key)
            pipeline.expire(key, self.window_seconds + 1)
            result = await pipeline.execute()

        return int(result[0])

    def _too_many_requests(
        self,
        *,
        limit: int,
        scope: str,
    ) -> JSONResponse:
        retry_after = self._seconds_until_reset()

        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded",
                "scope": scope,
                "retry_after": retry_after,
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(retry_after),
            },
        )

    @staticmethod
    def _normalize_path(path: str) -> str:
        if not path:
            return "/"

        normalized = "/" + path.strip("/")
        return normalized if normalized != "" else "/"

    @staticmethod
    def _token_fingerprint(token: str) -> str:
        return sha256(token.encode("utf-8")).hexdigest()
