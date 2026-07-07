import os
import socket
from uuid import uuid4


def resolve_worker_id() -> str:
    return os.getenv("SENTINEL_WORKER_ID") or f"{socket.gethostname()}-{uuid4().hex[:8]}"
