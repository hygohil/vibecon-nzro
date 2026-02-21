"""
Clear all seed data from the database
WARNING: This will delete all programs, farmers, claims, and ledger entries
"""
import asyncio
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']


async def clear_seed_data():
    """Clear all seeded data (except users and sessions)"""
    print("⚠️  WARNING: This will delete all programs, farmers, claims, and ledger data!")
    print("⏳ Starting cleanup in 2 seconds...")
    await asyncio.sleep(2)
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Delete all non-auth collections
    print("\n🗑️  Deleting programs...")
    result = await db.programs.delete_many({})
    print(f"   Deleted {result.deleted_count} programs")
    
    print("🗑️  Deleting farmers...")
    result = await db.farmers.delete_many({})
    print(f"   Deleted {result.deleted_count} farmers")
    
    print("🗑️  Deleting claims...")
    result = await db.claims.delete_many({})
    print(f"   Deleted {result.deleted_count} claims")
    
    print("🗑️  Deleting ledger entries...")
    result = await db.ledger.delete_many({})
    print(f"   Deleted {result.deleted_count} ledger entries")
    
    print("\n✅ Database cleared successfully!")
    print("   User accounts and sessions preserved.")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(clear_seed_data())
