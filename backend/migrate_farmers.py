"""
Migration script to:
1. Normalize land_type values (community -> leased, lowercase normalization)
2. Add unique index on phone number
"""
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def migrate_farmers():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['test_database']
    
    print("🔄 Starting farmers migration...")
    
    # Step 1: Normalize land_type values
    print("📋 Normalizing land_type values...")
    
    # Map 'community' to 'leased'
    result1 = await db.farmers.update_many(
        {"land_type": "community"},
        {"$set": {"land_type": "leased"}}
    )
    print(f"  ✓ Mapped {result1.modified_count} 'community' → 'leased'")
    
    # Normalize to lowercase (owned, leased, OWNED → owned, leased)
    farmers = await db.farmers.find({}, {"_id": 0, "farmer_id": 1, "land_type": 1}).to_list(10000)
    updated_count = 0
    for f in farmers:
        if f.get("land_type"):
            normalized = f["land_type"].lower()
            if normalized not in ["owned", "leased"]:
                # Default unknown types to 'owned'
                normalized = "owned"
            if normalized != f["land_type"]:
                await db.farmers.update_one(
                    {"farmer_id": f["farmer_id"]},
                    {"$set": {"land_type": normalized}}
                )
                updated_count += 1
    print(f"  ✓ Normalized {updated_count} land_type values to lowercase")
    
    # Step 2: Create unique index on phone
    print("📋 Creating unique index on phone...")
    try:
        await db.farmers.create_index("phone", unique=True)
        print("  ✓ Unique index created on phone field")
    except Exception as e:
        if "duplicate" in str(e).lower():
            print("  ⚠️  Duplicate phone numbers found! Cleaning up...")
            # Find duplicates
            pipeline = [
                {"$group": {"_id": "$phone", "count": {"$sum": 1}, "ids": {"$push": "$farmer_id"}}},
                {"$match": {"count": {"$gt": 1}}}
            ]
            duplicates = await db.farmers.aggregate(pipeline).to_list(100)
            print(f"  Found {len(duplicates)} duplicate phone numbers")
            
            # Keep first, mark others
            for dup in duplicates:
                phone = dup["_id"]
                ids = dup["ids"]
                print(f"  Phone {phone}: {len(ids)} farmers")
                # Keep first, append suffix to others
                for i, farmer_id in enumerate(ids[1:], 1):
                    new_phone = f"{phone}_dup{i}"
                    await db.farmers.update_one(
                        {"farmer_id": farmer_id},
                        {"$set": {"phone": new_phone}}
                    )
                    print(f"    Updated farmer {farmer_id}: {phone} → {new_phone}")
            
            # Try creating index again
            await db.farmers.create_index("phone", unique=True)
            print("  ✓ Unique index created after cleanup")
        else:
            print(f"  ✗ Error creating index: {e}")
    
    print("✅ Migration complete!")
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate_farmers())
