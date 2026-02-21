"""
Data seeding script for Aggregator OS
Creates sample programs, farmers, claims, and ledger entries for testing
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import random
import uuid

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

# Sample data constants
INDIAN_FIRST_NAMES = [
    "Rajesh", "Suresh", "Ramesh", "Mahesh", "Dinesh", "Ganesh", "Rakesh",
    "Amit", "Anil", "Vijay", "Ajay", "Sanjay", "Manoj", "Pramod", "Santosh",
    "Lakshmi", "Savitri", "Kamala", "Radha", "Sita", "Gita", "Priya", "Meera",
    "Sunita", "Anita", "Geeta", "Parvati", "Saraswati", "Durga", "Kali"
]

INDIAN_VILLAGES = [
    "Kothapalli", "Malkapuram", "Vemulapalli", "Venkatapuram", "Ramarajupalle",
    "Chintalapudi", "Amalapuram", "Tadepalligudem", "Narsapuram", "Bhimavaram",
    "Sattenapalle", "Mangalagiri", "Repalle", "Bapatla", "Chirala",
    "Piduguralla", "Vinukonda", "Narasaraopet", "Tenali", "Guntur",
    "Kandukur", "Ongole", "Markapur", "Addanki", "Giddalur",
    "Kanigiri", "Podili", "Darsi", "Yerragondapalem", "Tangutur"
]

DISTRICTS = [
    "Krishna", "Guntur", "Prakasam", "West Godavari", "East Godavari",
    "Visakhapatnam", "Vizianagaram", "Srikakulam", "Nellore", "Chittoor"
]

TREE_SPECIES = {
    "neem": {"growth_rate": "medium", "rate": 0.01, "bucket": "medium"},
    "mango": {"growth_rate": "medium", "rate": 0.01, "bucket": "medium"},
    "teak": {"growth_rate": "medium", "rate": 0.01, "bucket": "medium"},
    "banyan": {"growth_rate": "medium", "rate": 0.01, "bucket": "medium"},
    "peepal": {"growth_rate": "medium", "rate": 0.01, "bucket": "medium"},
    "eucalyptus": {"growth_rate": "fast_growing", "rate": 0.02, "bucket": "fast_growing"},
    "bamboo": {"growth_rate": "fast_growing", "rate": 0.02, "bucket": "fast_growing"},
    "moringa": {"growth_rate": "fast_growing", "rate": 0.02, "bucket": "fast_growing"},
    "jackfruit": {"growth_rate": "medium", "rate": 0.01, "bucket": "medium"},
    "tamarind": {"growth_rate": "slow", "rate": 0.005, "bucket": "slow"},
    "coconut": {"growth_rate": "slow", "rate": 0.005, "bucket": "slow"},
    "sandalwood": {"growth_rate": "slow", "rate": 0.005, "bucket": "slow"}
}

SAMPLE_PHOTO_URLS = [
    "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=800",  # tree planting
    "https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=800",  # sapling
    "https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?w=800",  # young tree
    "https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=800",  # plantation
    "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?w=800",  # tree row
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800",  # forest
    "https://images.unsplash.com/photo-1509715513011-e394f0cb20c4?w=800",  # green field
]

# Geo coordinates for different regions in Andhra Pradesh
REGION_COORDS = {
    "Krishna": {"lat_range": (16.5, 16.7), "lng_range": (80.5, 81.0)},
    "Guntur": {"lat_range": (16.0, 16.5), "lng_range": (80.0, 80.5)},
    "Prakasam": {"lat_range": (15.5, 16.0), "lng_range": (79.5, 80.0)},
    "West Godavari": {"lat_range": (16.7, 17.2), "lng_range": (81.0, 81.8)},
    "East Godavari": {"lat_range": (16.8, 17.5), "lng_range": (81.5, 82.3)},
}


def calculate_credits(tree_count: int, species: str, survival_rate: float, discount: float) -> float:
    """Calculate estimated carbon credits"""
    species_data = TREE_SPECIES.get(species.lower(), {"rate": 0.01})
    rate = species_data["rate"]
    return round(tree_count * rate * survival_rate * (1 - discount), 4)


def random_phone():
    """Generate random Indian phone number"""
    return f"+91{random.randint(7000000000, 9999999999)}"


def random_upi():
    """Generate random UPI ID"""
    name_part = random.choice(INDIAN_FIRST_NAMES).lower()
    return f"{name_part}{random.randint(100, 999)}@paytm"


def random_coords(district):
    """Generate random coordinates for a district"""
    coords = REGION_COORDS.get(district, {"lat_range": (16.0, 17.0), "lng_range": (80.0, 81.0)})
    lat = random.uniform(*coords["lat_range"])
    lng = random.uniform(*coords["lng_range"])
    return round(lat, 6), round(lng, 6)


async def seed_database(demo_mode=True):
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Clear existing data (optional - comment out if you want to keep existing data)
    print("🗑️  Clearing existing seed data...")
    # We'll only clear non-auth collections
    # await db.programs.delete_many({})
    # await db.farmers.delete_many({})
    # await db.claims.delete_many({})
    # await db.ledger.delete_many({})
    
    # Create or get demo user
    if demo_mode:
        print("🎭 Demo Mode: Creating/using demo account...")
        demo_user = await db.users.find_one({"email": "demo@aggregatoros.com"})
        if not demo_user:
            demo_user_id = "demo_user_permanent"
            await db.users.insert_one({
                "user_id": demo_user_id,
                "email": "demo@aggregatoros.com",
                "name": "Demo Account",
                "picture": "",
                "is_demo": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            demo_user = await db.users.find_one({"user_id": demo_user_id})
        else:
            # Clear existing demo data
            print("🗑️  Clearing existing demo account data...")
            await db.programs.delete_many({"user_id": demo_user["user_id"]})
            await db.farmers.delete_many({"program_id": {"$regex": "^demo_"}})
            await db.claims.delete_many({"program_id": {"$regex": "^demo_"}})
            await db.ledger.delete_many({"farmer_id": {"$regex": "^demo_"}})
        
        user_id = demo_user["user_id"]
        print(f"👤 Using DEMO user: {demo_user.get('email', 'N/A')} (ID: {user_id})")
    else:
        # Get or create a test user
        test_user = await db.users.find_one({"email": {"$exists": True}, "is_demo": {"$ne": True}})
        if not test_user:
            print("⚠️  No user found in database. Creating a test user...")
            test_user_id = f"user_{uuid.uuid4().hex[:12]}"
            await db.users.insert_one({
                "user_id": test_user_id,
                "email": "test@aggregatoros.com",
                "name": "Test Aggregator",
                "picture": "",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            test_user = await db.users.find_one({"user_id": test_user_id})
        
        user_id = test_user["user_id"]
        print(f"👤 Using user: {test_user.get('email', 'N/A')} (ID: {user_id})")
    
    # ═══════════════════════════════════════════════════════════
    # 1. CREATE PROGRAMS
    # ═══════════════════════════════════════════════════════════
    print("\n📋 Creating tree plantation programs...")
    
    programs_data = [
        {
            "name": "Coastal Green Belt Initiative",
            "region": "East Godavari",
            "description": "Coastal erosion control and mangrove restoration program along East Godavari coastline",
            "species_list": [
                {"name": "neem", "growth_rate": "medium"},
                {"name": "eucalyptus", "growth_rate": "fast_growing"},
                {"name": "coconut", "growth_rate": "slow"},
            ],
            "payout_rule_type": "per_tree",
            "payout_rate": 50.0,
            "survival_rate": 0.75,
            "conservative_discount": 0.15,
            "max_trees_per_acre": 500,
            "cooldown_days": 30,
            "required_proofs": ["location", "photo"],
            "monitoring_frequency_days": 90
        },
        {
            "name": "Krishna River Basin Afforestation",
            "region": "Krishna",
            "description": "Riparian forest restoration along Krishna river to prevent soil erosion and improve water quality",
            "species_list": [
                {"name": "bamboo", "growth_rate": "fast_growing"},
                {"name": "banyan", "growth_rate": "medium"},
                {"name": "peepal", "growth_rate": "medium"},
                {"name": "tamarind", "growth_rate": "slow"},
            ],
            "payout_rule_type": "per_tree",
            "payout_rate": 60.0,
            "survival_rate": 0.70,
            "conservative_discount": 0.20,
            "max_trees_per_acre": 400,
            "cooldown_days": 45,
            "required_proofs": ["location", "photo", "land_document"],
            "monitoring_frequency_days": 60
        },
        {
            "name": "Guntur Dryland Agroforestry",
            "region": "Guntur",
            "description": "Drought-resistant species for dryland farmers integrating trees with crops",
            "species_list": [
                {"name": "moringa", "growth_rate": "fast_growing"},
                {"name": "neem", "growth_rate": "medium"},
                {"name": "mango", "growth_rate": "medium"},
                {"name": "jackfruit", "growth_rate": "medium"},
            ],
            "payout_rule_type": "per_tree",
            "payout_rate": 45.0,
            "survival_rate": 0.65,
            "conservative_discount": 0.25,
            "max_trees_per_acre": 300,
            "cooldown_days": 30,
            "required_proofs": ["location", "photo"],
            "monitoring_frequency_days": 120
        },
        {
            "name": "Urban Fringe Carbon Sequestration",
            "region": "Guntur",
            "description": "Peri-urban afforestation program with high carbon sequestration potential",
            "species_list": [
                {"name": "teak", "growth_rate": "medium"},
                {"name": "sandalwood", "growth_rate": "slow"},
                {"name": "eucalyptus", "growth_rate": "fast_growing"},
            ],
            "payout_rule_type": "per_credit",
            "payout_rate": 500.0,  # per tCO2e
            "survival_rate": 0.80,
            "conservative_discount": 0.10,
            "max_trees_per_acre": 350,
            "cooldown_days": 60,
            "required_proofs": ["location", "photo", "land_document"],
            "monitoring_frequency_days": 90
        }
    ]
    
    created_programs = []
    for prog_data in programs_data:
        # Use demo_ prefix if demo mode
        prog_id = f"demo_prog_{uuid.uuid4().hex[:10]}" if user_id == "demo_user_permanent" else f"prog_{uuid.uuid4().hex[:10]}"
        doc = {
            "program_id": prog_id,
            "user_id": user_id,
            "status": "active",
            "farmers_count": 0,
            "claims_count": 0,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(60, 180))).isoformat(),
            **prog_data
        }
        await db.programs.insert_one(doc)
        created_programs.append(doc)
        print(f"  ✓ Created: {prog_data['name']}")
    
    # ═══════════════════════════════════════════════════════════
    # 2. CREATE FARMERS
    # ═══════════════════════════════════════════════════════════
    print("\n👨‍🌾 Creating farmers...")
    
    created_farmers = []
    farmers_per_program = [15, 20, 18, 12]  # Different farmer counts per program
    
    for idx, program in enumerate(created_programs):
        num_farmers = farmers_per_program[idx]
        district = program["region"]
        
        for i in range(num_farmers):
            # Use demo_ prefix if demo mode
            farmer_id = f"demo_farmer_{uuid.uuid4().hex[:10]}" if user_id == "demo_user_permanent" else f"farmer_{uuid.uuid4().hex[:10]}"
            name = random.choice(INDIAN_FIRST_NAMES) + " " + random.choice(["Kumar", "Rao", "Reddy", "Naidu", "Sharma"])
            
            farmer_doc = {
                "farmer_id": farmer_id,
                "name": name,
                "phone": random_phone(),
                "village": random.choice(INDIAN_VILLAGES),
                "district": district,
                "land_type": random.choice(["owned", "owned", "leased", "community"]),
                "acres": round(random.uniform(1.0, 10.0), 2),
                "upi_id": random_upi(),
                "program_id": program["program_id"],
                "program_name": program["name"],
                "status": "active",
                "total_trees": 0,
                "approved_trees": 0,
                "estimated_credits": 0.0,
                "total_payout": 0.0,
                "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(30, 150))).isoformat()
            }
            
            await db.farmers.insert_one(farmer_doc)
            created_farmers.append(farmer_doc)
        
        print(f"  ✓ Created {num_farmers} farmers for {program['name']}")
    
    print(f"  📊 Total farmers created: {len(created_farmers)}")
    
    # ═══════════════════════════════════════════════════════════
    # 3. CREATE CLAIMS
    # ═══════════════════════════════════════════════════════════
    print("\n📝 Creating tree plantation claims...")
    
    created_claims = []
    claim_statuses = ["approved", "approved", "approved", "pending", "rejected"]  # 60% approved
    
    for farmer in created_farmers:
        # Each farmer makes 2-5 claims
        num_claims = random.randint(2, 5)
        program = next(p for p in created_programs if p["program_id"] == farmer["program_id"])
        
        for i in range(num_claims):
            # Use demo_ prefix if demo mode
            claim_id = f"demo_claim_{uuid.uuid4().hex[:10]}" if farmer["farmer_id"].startswith("demo_") else f"claim_{uuid.uuid4().hex[:10]}"
            species = random.choice(list(TREE_SPECIES.keys()))
            tree_count = random.randint(20, 150)
            planted_date = (datetime.now(timezone.utc) - timedelta(days=random.randint(10, 120))).strftime("%Y-%m-%d")
            lat, lng = random_coords(farmer["district"])
            status = random.choice(claim_statuses)
            
            # Calculate credits
            survival = program["survival_rate"]
            discount = program["conservative_discount"]
            est_credits = calculate_credits(tree_count, species, survival, discount)
            
            # Calculate payout
            if program["payout_rule_type"] == "per_tree":
                est_payout = round(tree_count * program["payout_rate"], 2)
            else:
                est_payout = round(est_credits * program["payout_rate"], 2)
            
            claim_doc = {
                "claim_id": claim_id,
                "farmer_id": farmer["farmer_id"],
                "farmer_name": farmer["name"],
                "farmer_phone": farmer["phone"],
                "farmer_village": farmer["village"],
                "program_id": program["program_id"],
                "program_name": program["name"],
                "tree_count": tree_count,
                "species": species,
                "planted_date": planted_date,
                "lat": lat,
                "lng": lng,
                "photo_urls": random.sample(SAMPLE_PHOTO_URLS, k=random.randint(1, 3)),
                "notes": random.choice(["", "", "Near irrigation canal", "Boundary plantation", "Mixed with existing crops"]),
                "status": status,
                "estimated_credits": est_credits,
                "estimated_payout": est_payout,
                "verifier_notes": "" if status == "pending" else random.choice([
                    "Verified on-site. Good survival rate.",
                    "Photos and location confirmed.",
                    "Trees visible and healthy.",
                    "Duplicate location detected." if status == "rejected" else "",
                    "Suspicious timing between claims." if status == "rejected" else ""
                ]),
                "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(5, 100))).isoformat(),
                "approved_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 50))).isoformat() if status == "approved" else None
            }
            
            await db.claims.insert_one(claim_doc)
            created_claims.append(claim_doc)
            
            # Update farmer totals
            await db.farmers.update_one(
                {"farmer_id": farmer["farmer_id"]},
                {"$inc": {"total_trees": tree_count}}
            )
            
            if status == "approved":
                await db.farmers.update_one(
                    {"farmer_id": farmer["farmer_id"]},
                    {
                        "$inc": {
                            "approved_trees": tree_count,
                            "estimated_credits": est_credits,
                            "total_payout": est_payout
                        }
                    }
                )
    
    print(f"  📊 Total claims created: {len(created_claims)}")
    print(f"  ✅ Approved: {len([c for c in created_claims if c['status'] == 'approved'])}")
    print(f"  ⏳ Pending: {len([c for c in created_claims if c['status'] == 'pending'])}")
    print(f"  ❌ Rejected: {len([c for c in created_claims if c['status'] == 'rejected'])}")
    
    # ═══════════════════════════════════════════════════════════
    # 4. CREATE LEDGER ENTRIES
    # ═══════════════════════════════════════════════════════════
    print("\n💰 Creating ledger entries...")
    
    ledger_count = 0
    for farmer in created_farmers:
        # Only create ledger entry for farmers with approved claims
        approved_claims = [c for c in created_claims if c["farmer_id"] == farmer["farmer_id"] and c["status"] == "approved"]
        
        if approved_claims:
            total_trees = sum(c["tree_count"] for c in approved_claims)
            total_credits = sum(c["estimated_credits"] for c in approved_claims)
            total_payout = sum(c["estimated_payout"] for c in approved_claims)
            
            # Some farmers have been paid partially
            paid_amount = 0.0
            if random.random() > 0.5:  # 50% chance of partial payment
                paid_amount = round(total_payout * random.uniform(0.3, 0.9), 2)
            
            # Use demo_ prefix if demo mode
            ledger_id = f"demo_ledger_{uuid.uuid4().hex[:10]}" if farmer["farmer_id"].startswith("demo_") else f"ledger_{uuid.uuid4().hex[:10]}"
            ledger_doc = {
                "ledger_id": ledger_id,
                "farmer_id": farmer["farmer_id"],
                "farmer_name": farmer["name"],
                "farmer_phone": farmer["phone"],
                "farmer_village": farmer["village"],
                "upi_id": farmer.get("upi_id", ""),
                "program_id": farmer["program_id"],
                "approved_trees_total": total_trees,
                "approved_credits_total": round(total_credits, 4),
                "payable_amount": round(total_payout, 2),
                "paid_amount": paid_amount,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.ledger.insert_one(ledger_doc)
            ledger_count += 1
    
    print(f"  ✓ Created {ledger_count} ledger entries")
    
    # ═══════════════════════════════════════════════════════════
    # 5. UPDATE PROGRAM COUNTS
    # ═══════════════════════════════════════════════════════════
    print("\n🔄 Updating program statistics...")
    
    for program in created_programs:
        farmers_count = await db.farmers.count_documents({"program_id": program["program_id"]})
        claims_count = await db.claims.count_documents({"program_id": program["program_id"]})
        
        await db.programs.update_one(
            {"program_id": program["program_id"]},
            {"$set": {"farmers_count": farmers_count, "claims_count": claims_count}}
        )
    
    # ═══════════════════════════════════════════════════════════
    # 6. SUMMARY
    # ═══════════════════════════════════════════════════════════
    print("\n" + "="*60)
    print("✅ DATABASE SEEDING COMPLETE!")
    print("="*60)
    print(f"👤 User: {test_user.get('email', 'N/A')}")
    print(f"📋 Programs: {len(created_programs)}")
    print(f"👨‍🌾 Farmers: {len(created_farmers)}")
    print(f"📝 Claims: {len(created_claims)}")
    print(f"💰 Ledger entries: {ledger_count}")
    
    # Calculate totals
    total_trees_approved = sum(c["tree_count"] for c in created_claims if c["status"] == "approved")
    total_credits = sum(c["estimated_credits"] for c in created_claims if c["status"] == "approved")
    total_payout = sum(c["estimated_payout"] for c in created_claims if c["status"] == "approved")
    
    print(f"\n🌳 Total approved trees: {total_trees_approved}")
    print(f"🌍 Total estimated credits: {total_credits:.4f} tCO₂e")
    print(f"💵 Total payable amount: ₹{total_payout:.2f}")
    print("="*60)
    
    client.close()
    print("\n🎉 Ready for testing!")


if __name__ == "__main__":
    asyncio.run(seed_database())
