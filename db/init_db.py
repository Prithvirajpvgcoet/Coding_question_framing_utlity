"""
Run once to create all tables and seed the dev client.

Usage:
    python db/init_db.py

Requires Postgres to be running and DATABASE_URL set in .env.
"""
import asyncio
import uuid
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import text
from db.session import async_engine
from db.models import Base


async def init():
    print("Connecting to database...")
    async with async_engine.begin() as conn:
        print("Creating extensions...")
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\""))
        except Exception:
            pass  # pgcrypto may already exist

        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            print("  vector extension ready.")
        except Exception as e:
            print(f"  Warning: vector extension skipped ({e})")

        print("Creating tables from ORM models...")
        await conn.run_sync(Base.metadata.create_all)
        print("  Tables created.")

        # Seed dev client if not exists
        print("Seeding dev client...")
        dev_id = "00000000-0000-0000-0000-000000000001"
        try:
            await conn.execute(text("""
                INSERT INTO clients (id, name, api_key_hash, is_active)
                VALUES (:id, :name, :hash, TRUE)
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": dev_id,
                "name": "Dev Client",
                "hash": "dev-key-plain",   # auth.py accepts any key in dev mode
            })
            print(f"  Dev client seeded: {dev_id}")
        except Exception as e:
            print(f"  Dev client already exists or seeding skipped: {e}")

    print("\nDatabase initialisation complete.")
    print("You can now start the server: python -m uvicorn api.main:app --reload --port 8000")


if __name__ == "__main__":
    asyncio.run(init())
