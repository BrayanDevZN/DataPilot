"""FastAPI application composition for the DataPilot backend."""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.infra.manage import settings

from .handles import PUBLIC_ROUTES, routers
from .middleware import Middleware


class ApiInstance:
    def __init__(self) -> None:
        self.app: FastAPI = FastAPI(
            title="DataPilot API",
            version="1.0.0",
        )
        self.routers: list[APIRouter] = list(routers)

    def configure_cors(self) -> None:
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_allowed_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def configure_middleware(self) -> None:
        self.app.add_middleware(
            Middleware,
            public_routes=PUBLIC_ROUTES,
        )

    def include_routers(self) -> None:
        for router in self.routers:
            self.app.include_router(router)

    def build(self) -> FastAPI:
        self.configure_cors()
        self.configure_middleware()
        self.include_routers()
        return self.app


api_instance = ApiInstance()
app = api_instance.build()
