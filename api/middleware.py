import time
from collections import defaultdict
from threading import Lock

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    # NOTE: This implementation uses per-worker in-memory storage.
    # With multiple uvicorn workers, rate limits are per-worker, not global.
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.client_calls: dict[str, list[float]] = defaultdict(list)
        self.lock = Lock()

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        with self.lock:
            self.client_calls[client_ip] = [
                timestamp
                for timestamp in self.client_calls[client_ip]
                if current_time - timestamp < 60
            ]

            if len(self.client_calls[client_ip]) >= self.calls_per_minute:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded. Please try again later."},
                )

            self.client_calls[client_ip].append(current_time)

        response = await call_next(request)
        return response
