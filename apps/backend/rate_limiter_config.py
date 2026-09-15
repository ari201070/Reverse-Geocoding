# Rate Limiter Configuration
# Centralized constants for easy adjustment without touching business logic

import os

# Database path - use the same photo_catalog.db as single source of truth
SQLITE_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "photo_catalog.db"
)

# Rate limiting thresholds
RATE_LIMIT_REQUESTS = 100  # Maximum requests per window
RATE_LIMIT_WINDOW_SECONDS = 60  # Window size in seconds (1 minute)

# Cleanup configuration
CLEANUP_INTERVAL_SECONDS = 600  # Run cleanup every 10 minutes
WINDOW_RETENTION_MINUTES = 15  # Keep records for 15 minutes