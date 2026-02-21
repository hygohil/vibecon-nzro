"""
View database statistics
Shows counts of all collections and sample data
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


async def view_stats():
    """Display database statistics"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("\n" + "="*60)
    print("📊 DATABASE STATISTICS")
    print("="*60)
    
    # Collections count
    print("\n📦 Collections:")
    users_count = await db.users.count_documents({})
    programs_count = await db.programs.count_documents({})
    farmers_count = await db.farmers.count_documents({})
    claims_count = await db.claims.count_documents({})
    ledger_count = await db.ledger.count_documents({})
    
    print(f"   👤 Users: {users_count}")
    print(f"   📋 Programs: {programs_count}")
    print(f"   👨‍🌾 Farmers: {farmers_count}")
    print(f"   📝 Claims: {claims_count}")
    print(f"   💰 Ledger entries: {ledger_count}")
    
    # Claims breakdown
    if claims_count > 0:
        print("\n📝 Claims Status:")
        pending = await db.claims.count_documents({"status": "pending"})
        approved = await db.claims.count_documents({"status": "approved"})
        rejected = await db.claims.count_documents({"status": "rejected"})
        needs_info = await db.claims.count_documents({"status": "needs_info"})
        
        print(f"   ⏳ Pending: {pending}")
        print(f"   ✅ Approved: {approved}")
        print(f"   ❌ Rejected: {rejected}")
        print(f"   ℹ️  Needs Info: {needs_info}")
        
        # Aggregated totals
        pipeline = [
            {"$match": {"status": "approved"}},
            {"$group": {
                "_id": None,
                "total_trees": {"$sum": "$tree_count"},
                "total_credits": {"$sum": "$estimated_credits"},
                "total_payout": {"$sum": "$estimated_payout"}
            }}
        ]
        agg = await db.claims.aggregate(pipeline).to_list(1)
        if agg:
            totals = agg[0]
            print(f"\n🌳 Approved Totals:")
            print(f"   Trees: {totals.get('total_trees', 0)}")
            print(f"   Credits: {totals.get('total_credits', 0):.4f} tCO₂e")
            print(f"   Payout: ₹{totals.get('total_payout', 0):.2f}")
    
    # Sample programs
    if programs_count > 0:
        print("\n📋 Sample Programs:")
        programs = await db.programs.find({}, {"_id": 0, "program_id": 1, "name": 1, "region": 1}).to_list(5)
        for p in programs:
            print(f"   • {p.get('name', 'N/A')} ({p.get('region', 'N/A')})")
    
    # Sample farmers
    if farmers_count > 0:
        print("\n👨‍🌾 Sample Farmers:")
        farmers = await db.farmers.find({}, {"_id": 0, "name": 1, "village": 1, "total_trees": 1, "approved_trees": 1}).to_list(5)
        for f in farmers:
            print(f"   • {f.get('name', 'N/A')} from {f.get('village', 'N/A')} - {f.get('approved_trees', 0)}/{f.get('total_trees', 0)} trees approved")
    
    print("\n" + "="*60)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(view_stats())
