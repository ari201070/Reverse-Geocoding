import aiosqlite
from rate_limiter_config import SQLITE_DB_PATH, WINDOW_RETENTION_MINUTES


async def init_db():
    """Initialize the rate limiting database table with WAL mode for better performance."""
    async with aiosqlite.connect(SQLITE_DB_PATH) as db:
        # Enable WAL mode for better concurrent read/write performance
        await db.execute("PRAGMA journal_mode=WAL;")
        
        # Create rate limiting table if it doesn't exist
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_rate_limits (
                ip TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                window_start INTEGER NOT NULL,
                count INTEGER DEFAULT 1,
                PRIMARY KEY (ip, endpoint, window_start)
            )
        """)
        
        # Create index for efficient lookups
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_rate_lookup 
            ON api_rate_limits(ip, endpoint, window_start)
        """)
        
        await db.commit()


async def increment_and_check(ip: str, endpoint: str, window_start: int) -> tuple[bool, int]:
    """
    Increment the request count for a given IP/endpoint/window and check if within limit.
    
    Returns:
        tuple: (is_within_limit, current_count)
    """
    async with aiosqlite.connect(SQLITE_DB_PATH) as db:
        # Insert or increment the counter
        await db.execute("""
            INSERT INTO api_rate_limits (ip, endpoint, window_start, count) 
            VALUES (?, ?, ?, 1)
            ON CONFLICT(ip, endpoint, window_start) 
            DO UPDATE SET count = count + 1
        """, (ip, endpoint, window_start))
        
        await db.commit()
        
        # Get the updated count
        cursor = await db.execute(
            "SELECT count FROM api_rate_limits WHERE ip = ? AND endpoint = ? AND window_start = ?",
            (ip, endpoint, window_start)
        )
        row = await cursor.fetchone()
        current_count = row[0] if row else 1
        
        # Check against limit (import here to avoid circular imports)
        from rate_limiter_config import RATE_LIMIT_REQUESTS
        is_within_limit = current_count <= RATE_LIMIT_REQUESTS
        
        return (is_within_limit, current_count)


async def cleanup_old_windows(current_window: int):
    """Clean up old rate limiting records to keep the database lightweight."""
    async with aiosqlite.connect(SQLITE_DB_PATH) as db:
        # Calculate the cutoff window (current_window - retention_minutes)
        cutoff_window = current_window - (WINDOW_RETENTION_MINUTES // 60 + 1)
        
        await db.execute(
            "DELETE FROM api_rate_limits WHERE window_start < ?",
            (cutoff_window,)
        )
        
        await db.commit()