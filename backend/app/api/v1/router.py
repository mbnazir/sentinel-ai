from fastapi import APIRouter

from app.platform.routing.register_routers import register_routers
from app.platform.routing.router_registry import ROUTER_REGISTRY

api_v1_router = register_routers(APIRouter(), ROUTER_REGISTRY)
