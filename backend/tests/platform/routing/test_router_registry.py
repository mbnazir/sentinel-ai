from app.platform.routing.router_registry import ROUTER_REGISTRY


def test_router_registry_prefixes_are_unique() -> None:
    prefixes = [definition.prefix for definition in ROUTER_REGISTRY]

    assert len(prefixes) == len(set(prefixes))


def test_router_registry_contains_expected_core_routes() -> None:
    prefixes = {definition.prefix for definition in ROUTER_REGISTRY}

    assert "/health" in prefixes
    assert "/timelines" in prefixes
    assert "/anomaly" in prefixes
    assert "/investigation-queue" in prefixes
