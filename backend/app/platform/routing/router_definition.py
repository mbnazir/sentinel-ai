from dataclasses import dataclass
from fastapi import APIRouter


@dataclass(frozen=True)
class RouterDefinition:
    router: APIRouter
    prefix: str
    tags: list[str]
