import asyncio
from time import monotonic

class AsyncRateLimiter:
    def __init__(self, rate_per_second:float):
        if rate_per_second<=0: raise ValueError("rate_per_second must be > 0")
        self.interval=1.0/rate_per_second
        self._last=0.0
        self._lock=asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now=monotonic()
            wait=self.interval-(now-self._last)
            if wait>0: await asyncio.sleep(wait)
            self._last=monotonic()
