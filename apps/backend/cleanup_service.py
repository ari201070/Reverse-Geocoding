import time
import asyncio
from rate_limiter_config import RATE_LIMIT_WINDOW_SECONDS, CLEANUP_INTERVAL_SECONDS
from sqlite_rate_store import cleanup_old_windows


async def rate_limit_cleanup_loop():
    """
    Background task to clean up old rate limiting records.
    Runs periodically to keep the database lightweight.
    """
    while True:
        try:
            # Wait for the cleanup interval
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            
            # Calculate current window
            current_window = int(time.time()) // RATE_LIMIT_WINDOW_SECONDS
            
            # Clean up old windows
            await cleanup_old_windows(current_window)
            
            print(f"[RATE_LIMITER] Cleaned up old windows. Current window: {current_window}")
            
        except Exception as e:
            print(f"[RATE_LIMITER] Cleanup error: {e}")
            # Wait a bit before retrying on error
            await asyncio.sleep(60)


def start_cleanup_task():
    """Start the background cleanup task."""
    asyncio.create_task(rate_limit_cleanup_loop())