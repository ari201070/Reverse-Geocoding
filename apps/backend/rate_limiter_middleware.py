import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from rate_limiter_config import RATE_LIMIT_WINDOW_SECONDS
from sqlite_rate_store import increment_and_check


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting API requests using SQLite.
    Tracks requests by IP and endpoint within time windows.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/api/health", "/favicon.ico", "/"]:
            return await call_next(request)
        
        # Get client IP and endpoint
        ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        
        # Calculate current time window
        current_window = int(time.time()) // RATE_LIMIT_WINDOW_SECONDS
        
        # Check and increment the rate limit counter
        try:
            is_within_limit, current_count = await increment_and_check(ip, endpoint, current_window)
        except Exception as e:
            # If rate limiting fails, allow the request but log the error
            print(f"Rate limiting error: {e}")
            return await call_next(request)
        
        # If rate limit exceeded, return 429 Too Many Requests
        if not is_within_limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests to {endpoint}. Try again later.",
                    "retry_after": RATE_LIMIT_WINDOW_SECONDS
                }
            )
        
        # Process the request normally
        response = await call_next(request)
        
        # Add rate limit headers to the response
        response.headers["X-RateLimit-Limit"] = "100"
        response.headers["X-RateLimit-Remaining"] = str(max(0, 100 - current_count))
        response.headers["X-RateLimit-Reset"] = str((current_window + 1) * RATE_LIMIT_WINDOW_SECONDS)
        
        return response