"""
ANVESHAK — Unified Native Startup
Starts the FastAPI application and the Live Ingestor concurrently for local native testing.
Also configures a local SQLite database if no Postgres URL is provided.
"""

import os
import asyncio
import sys

# Set SQLite as the fallback database if running natively without Docker
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./anveshak_local.db"
    
import uvicorn
from app.services.live_ingestor import run_continuous_ingestor

async def start_fastapi():
    """Run the Uvicorn server."""
    config = uvicorn.Config("app.main:app", host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    """Run both the FastAPI server and the continuous live ingestor."""
    print("="*60)
    print("🌌 Starting ANVESHAK Pipeline in Native Mode 🌌")
    print("Database:", os.environ["DATABASE_URL"])
    print("="*60)
    
    # Run both the web server and the background data puller
    await asyncio.gather(
        start_fastapi(),
        run_continuous_ingestor()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down ANVESHAK...")
