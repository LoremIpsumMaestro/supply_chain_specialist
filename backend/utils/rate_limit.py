"""Rate limiting utilities."""

import time
from collections import defaultdict
from functools import wraps
from typing import Callable, Dict
from uuid import UUID

from fastapi import HTTPException, status


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self):
        self.requests: Dict[UUID, list[float]] = defaultdict(list)

    def check_rate_limit(
        self, user_id: UUID, max_requests: int, window_seconds: int
    ) -> bool:
        """
        Check if user has exceeded rate limit.

        Args:
            user_id: User's UUID
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if within rate limit, False otherwise
        """
        current_time = time.time()
        user_requests = self.requests[user_id]

        # Remove old requests outside the window
        cutoff_time = current_time - window_seconds
        user_requests[:] = [req_time for req_time in user_requests if req_time > cutoff_time]

        # Check if limit exceeded
        if len(user_requests) >= max_requests:
            return False

        # Add current request
        user_requests.append(current_time)
        return True


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 10, window_seconds: int = 60) -> Callable:
    """
    Decorator for rate limiting endpoints.

    Args:
        max_requests: Maximum number of requests allowed (default: 10)
        window_seconds: Time window in seconds (default: 60)

    Usage:
        @rate_limit(max_requests=10, window_seconds=60)
        async def my_endpoint(user_id: UUID = Depends(get_current_user_id)):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id from kwargs (injected by get_current_user_id dependency)
            user_id = kwargs.get("user_id")

            if user_id and not _rate_limiter.check_rate_limit(
                user_id, max_requests, window_seconds
            ):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds} seconds.",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
