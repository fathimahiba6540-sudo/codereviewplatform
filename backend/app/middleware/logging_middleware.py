import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from backend.app.core.logging import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking request latency and attaching unique request IDs."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Add request_id to state
        request.state.request_id = request_id

        logger.info(f"--> Incoming [{request_id}] {request.method} {request.url.path}")

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-MS"] = f"{process_time:.2f}"

            logger.info(
                f"<-- Completed [{request_id}] {request.method} {request.url.path} "
                f"Status: {response.status_code} in {process_time:.2f}ms"
            )
            return response
        except Exception as exc:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"<-- Failed [{request_id}] {request.method} {request.url.path} "
                f"Error: {str(exc)} in {process_time:.2f}ms"
            )
            raise exc
