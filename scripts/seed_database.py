"""
Seed Database Script
Loads all seed datasets from data/seed_references/ into PostgreSQL.
"""
import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db.session import get_session
from services.dataset_ingestion import load_seed_datasets

async def main():
    print("Connecting to PostgreSQL...")
    try:
        async with get_session() as db:
            print("Database connected. Ingesting seed reference files from data/seed_references/...")
            records = await load_seed_datasets(db=db, client_id="00000000-0000-0000-0000-000000000001")
            print(f"Successfully ingested {len(records)} records into PostgreSQL table 'reference_documents'!")
            for r in records:
                print(f"  - [{r.get('doc_type', 'DOMAIN_SCENARIO')}] {r.get('title')} ({r.get('topic')})")
    except Exception as e:
        print(f"Error during seeding: {e}")
        print("\nNote: If PostgreSQL is offline, please start Docker and run:")
        print("  docker-compose up -d postgres")
        print("Then re-run this script.")

if __name__ == "__main__":
    asyncio.run(main())
