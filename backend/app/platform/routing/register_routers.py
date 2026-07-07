from fastapi import APIRouter

from app.platform.routing.router_definition import RouterDefinition


class RouterRegistrationError(ValueError):
    pass


def register_routers(api_router: APIRouter, registry: list[RouterDefinition]) -> APIRouter:
    seen_prefixes: set[str] = set()

    for definition in registry:
        if definition.prefix in seen_prefixes:
            raise RouterRegistrationError(f"Duplicate API route prefix registered: {definition.prefix}")

        seen_prefixes.add(definition.prefix)
        api_router.include_router(
            definition.router,
            prefix=definition.prefix,
            tags=definition.tags,
        )

    return api_router
