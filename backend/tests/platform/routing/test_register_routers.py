from fastapi import APIRouter

from app.platform.routing.register_routers import RouterRegistrationError, register_routers
from app.platform.routing.router_definition import RouterDefinition


def test_register_routers_adds_routes() -> None:
    child = APIRouter()

    @child.get("/ping")
    def ping():
        return {"ok": True}

    parent = APIRouter()
    register_routers(parent, [RouterDefinition(child, "/child", ["Child"])])

    assert len(parent.routes) == 1


def test_register_routers_rejects_duplicate_prefixes() -> None:
    child = APIRouter()
    parent = APIRouter()

    try:
        register_routers(
            parent,
            [
                RouterDefinition(child, "/x", ["X"]),
                RouterDefinition(child, "/x", ["X2"]),
            ],
        )
    except RouterRegistrationError:
        assert True
    else:
        assert False, "Expected duplicate prefix error"
