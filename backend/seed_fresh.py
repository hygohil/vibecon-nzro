"""
Fresh seed script for VanaLedger (updated schema)
- projects, farmers, activities, ledger, credits, benefit_shares
- Proper Indian names, 10-digit mobile numbers, no village/district
"""
import asyncio
import os
import random
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

# ── Realistic Indian Full Names (Telugu/Andhra Pradesh region) ──
FARMER_NAMES = [
    "Venkatesh Reddy", "Srinivasa Rao", "Ramakrishna Naidu", "Subrahmanyam Goud",
    "Lakshminarayana Pillai", "Narasimha Raju", "Venkataramana Yadav", "Tirupathi Varma",
    "Raghavendra Murthy", "Krishnamurthy Iyer", "Satyanarayana Babu", "Anjaneyulu Prasad",
    "Balakrishna Sharma", "Chandrasekhar Rao", "Durgaprasad Reddy", "Eswaraiah Naidu",
    "Gangadhara Rao", "Hanumantha Rao", "Iswaraiah Goud", "Jaganmohan Reddy",
    "Koteswara Rao", "Lakshmipathi Naidu", "Mallikarjuna Rao", "Nageswara Rao",
    "Obulaiah Reddy", "Pulla Reddy", "Ramalingaiah Naidu", "Sivaprasad Rao",
    "Thirupathaiah Raju", "Umamaheswar Rao", "Veeraiah Naidu", "Yellaiah Goud",
    "Anantha Reddy", "Bhaskara Rao", "Chinnaiah Naidu", "Devaiah Reddy",
    "Eswar Prasad", "Govinda Rao", "Harish Kumar", "Ippaiah Reddy",
    "Jayaram Naidu", "Kishore Babu", "Lakshman Rao", "Manohar Reddy",
    "Narayan Das", "Omkar Reddy", "Prasanna Kumar", "Rajasekhar Rao",
    "Savitha Devi", "Tulasi Devi", "Usha Rani", "Vasantha Kumari",
    "Sujatha Bai", "Padmavathi Reddy", "Kamakshi Naidu", "Bhavani Devi",
    "Annapurna Rao", "Saraswathi Devi", "Meenakshi Amma", "Radhabai Reddy",
    "Nagamani Devi", "Indira Bai", "Jhansi Rani", "Lalitha Kumari",
    "Manjula Devi", "Nirmala Bai"
]

# ── 10-digit mobile numbers (no country code) ──
def gen_phone(used: set) -> str:
    while True:
        prefix = random.choice([6, 7, 8, 9])
        num = f"{prefix}{random.randint(100000000, 999999999)}"
        if num not in used:
            used.add(num)
            return num

def gen_upi(name: str) -> str:
    slug = name.split()[0].lower()
    return f"{slug}{random.randint(10, 99)}@{random.choice(['paytm', 'gpay', 'phonepe', 'ybl', 'oksbi'])}"

SAMPLE_PHOTOS = [
    "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=800",
    "https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=800",
    "https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?w=800",
    "https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=800",
    "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?w=800",
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800",
    "https://images.unsplash.com/photo-1509715513011-e394f0cb20c4?w=800",
]

REGION_COORDS = {
    "East Godavari":    {"lat": (16.8, 17.3), "lng": (81.5, 82.2)},
    "Krishna":          {"lat": (16.4, 16.8), "lng": (80.5, 81.2)},
    "Guntur":           {"lat": (16.0, 16.5), "lng": (79.8, 80.5)},
    "Vizianagaram":     {"lat": (18.0, 18.5), "lng": (83.2, 83.8)},
}

def rcoords(region):
    c = REGION_COORDS.get(region, {"lat": (16.0, 17.0), "lng": (80.0, 81.0)})
    return round(random.uniform(*c["lat"]), 6), round(random.uniform(*c["lng"]), 6)

SPECIES_RATES = {
    "eucalyptus": 0.02, "bamboo": 0.02, "moringa": 0.02,
    "neem": 0.01, "mango": 0.01, "teak": 0.01, "banyan": 0.01, "peepal": 0.01,
    "tamarind": 0.005, "coconut": 0.005, "sandalwood": 0.005, "jackfruit": 0.01,
}

def calc_credits(tree_count, species, survival, discount):
    rate = SPECIES_RATES.get(species.lower(), 0.01)
    return round(tree_count * rate * survival * (1 - discount), 4)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def past_iso(days_ago):
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()

def date_str(days_ago):
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%d")


async def run():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    # ── 1. Clear all data except auth ──────────────────────────
    print("Clearing existing data (keeping auth)...")
    await db.projects.delete_many({})
    await db.farmers.delete_many({})
    await db.activities.delete_many({})
    await db.ledger.delete_many({})
    await db.credits.delete_many({})
    await db.benefit_shares.delete_many({})
    print("  Done.")

    # ── 2. Ensure demo user ────────────────────────────────────
    demo_user = await db.users.find_one({"email": "demo@aggregatoros.com"}, {"_id": 0})
    if not demo_user:
        user_id = "demo_user_permanent"
        await db.users.insert_one({
            "user_id": user_id,
            "email": "demo@aggregatoros.com",
            "name": "Demo Aggregator",
            "picture": "",
            "is_demo": True,
            "created_at": now_iso()
        })
        print("  Created demo user.")
    else:
        user_id = demo_user["user_id"]
        print(f"  Using existing demo user: {user_id}")

    # ── 3. Create Projects ─────────────────────────────────────
    print("\nCreating projects...")

    PROJECTS = [
        {
            "project_id": "proj_coastal_001",
            "name": "Coastal Green Belt Initiative",
            "region": "East Godavari",
            "description": "Coastal erosion control and mangrove restoration along East Godavari coastline. Focuses on salt-tolerant species for long-term ecosystem stability.",
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
            "monitoring_frequency_days": 90,
            "created_at": past_iso(180),
        },
        {
            "project_id": "proj_krishna_002",
            "name": "Krishna River Basin Afforestation",
            "region": "Krishna",
            "description": "Riparian forest restoration along Krishna river to prevent soil erosion and improve water quality. Community-led agroforestry model.",
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
            "monitoring_frequency_days": 60,
            "created_at": past_iso(150),
        },
        {
            "project_id": "proj_guntur_003",
            "name": "Guntur Dryland Agroforestry",
            "region": "Guntur",
            "description": "Drought-resistant species integrated with existing crops. Designed for small and marginal farmers in semi-arid Guntur district.",
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
            "monitoring_frequency_days": 120,
            "created_at": past_iso(120),
        },
        {
            "project_id": "proj_vizag_004",
            "name": "Vizianagaram Tribal Forestry",
            "region": "Vizianagaram",
            "description": "High-value timber and carbon sequestration program with tribal communities in Vizianagaram hills. Premium species for long-term income.",
            "species_list": [
                {"name": "teak", "growth_rate": "medium"},
                {"name": "sandalwood", "growth_rate": "slow"},
                {"name": "bamboo", "growth_rate": "fast_growing"},
            ],
            "payout_rule_type": "per_credit",
            "payout_rate": 500.0,
            "survival_rate": 0.80,
            "conservative_discount": 0.10,
            "max_trees_per_acre": 350,
            "cooldown_days": 60,
            "required_proofs": ["location", "photo", "land_document"],
            "monitoring_frequency_days": 90,
            "created_at": past_iso(90),
        },
    ]

    for p in PROJECTS:
        p["user_id"] = user_id
        p["status"] = "active"
        p["farmers_count"] = 0
        p["activities_count"] = 0
        await db.projects.insert_one(p)
        print(f"  + {p['name']}")

    # ── 4. Create Farmers ──────────────────────────────────────
    print("\nCreating farmers...")

    used_phones = set()
    used_names = list(FARMER_NAMES)
    random.shuffle(used_names)

    # Distribute farmers: 18, 20, 16, 11 = 65 total
    FARMER_DIST = {
        "proj_coastal_001": (0, 18),
        "proj_krishna_002": (18, 38),
        "proj_guntur_003": (38, 54),
        "proj_vizag_004": (54, 65),
    }

    all_farmers = []
    for proj_id, (start, end) in FARMER_DIST.items():
        proj = next(p for p in PROJECTS if p["project_id"] == proj_id)
        chunk = used_names[start:end]
        for name in chunk:
            phone = gen_phone(used_phones)
            acres = round(random.uniform(1.5, 8.5), 2)
            farmer = {
                "farmer_id": f"farmer_{uuid.uuid4().hex[:10]}",
                "name": name,
                "phone": phone,
                "land_type": random.choice(["owned", "owned", "leased"]),
                "acres": acres,
                "upi_id": gen_upi(name),
                "project_id": proj_id,
                "project_name": proj["name"],
                "status": "active",
                "total_trees": 0,
                "approved_trees": 0,
                "estimated_credits": 0.0,
                "total_payout": 0.0,
                "created_at": past_iso(random.randint(30, 160)),
            }
            await db.farmers.insert_one(farmer)
            all_farmers.append(farmer)
    print(f"  Created {len(all_farmers)} farmers.")

    # ── 5. Create Activities ───────────────────────────────────
    print("\nCreating plantation activities...")

    SPECIES_BY_PROJECT = {
        "proj_coastal_001": ["neem", "eucalyptus", "coconut"],
        "proj_krishna_002": ["bamboo", "banyan", "peepal", "tamarind"],
        "proj_guntur_003": ["moringa", "neem", "mango", "jackfruit"],
        "proj_vizag_004": ["teak", "sandalwood", "bamboo"],
    }

    VERIFIER_NOTES_APPROVED = [
        "Verified on-site. Trees healthy and well-spaced.",
        "Photos and GPS location confirmed. Good survival rate.",
        "Field visit completed. Saplings in excellent condition.",
        "Geo-tagged evidence matches submitted location.",
        "Trees visible and growing. Boundary plantation confirmed.",
    ]
    VERIFIER_NOTES_REJECTED = [
        "Coordinates do not match farmer's registered land.",
        "Duplicate location from another farmer's submission.",
        "Photo evidence insufficient or blurry.",
        "Planted outside project boundary.",
    ]

    all_activities = []
    # Status weights: 60% approved, 20% pending, 20% rejected
    STATUS_POOL = ["approved"] * 6 + ["pending"] * 2 + ["rejected"] * 2

    for farmer in all_farmers:
        proj = next(p for p in PROJECTS if p["project_id"] == farmer["project_id"])
        num_acts = random.randint(2, 5)
        species_pool = SPECIES_BY_PROJECT[farmer["project_id"]]

        for _ in range(num_acts):
            species = random.choice(species_pool)
            tree_count = random.randint(25, 200)
            status = random.choice(STATUS_POOL)
            survival = proj["survival_rate"]
            discount = proj["conservative_discount"]
            est_credits = calc_credits(tree_count, species, survival, discount)

            if proj["payout_rule_type"] == "per_tree":
                est_payout = round(tree_count * proj["payout_rate"], 2)
            else:
                est_payout = round(est_credits * proj["payout_rate"], 2)

            lat, lng = rcoords(proj["region"])
            created_days_ago = random.randint(5, 100)

            act = {
                "activity_id": f"activity_{uuid.uuid4().hex[:10]}",
                "farmer_id": farmer["farmer_id"],
                "farmer_name": farmer["name"],
                "farmer_phone": farmer["phone"],
                "project_id": farmer["project_id"],
                "project_name": farmer["project_name"],
                "tree_count": tree_count,
                "species": species,
                "planted_date": date_str(created_days_ago + 5),
                "lat": lat,
                "lng": lng,
                "photo_urls": random.sample(SAMPLE_PHOTOS, k=random.randint(1, 3)),
                "notes": random.choice(["", "Near irrigation canal", "Boundary plantation", "Mixed with existing crops", ""]),
                "status": status,
                "estimated_credits": est_credits,
                "estimated_payout": est_payout,
                "verifier_notes": (
                    random.choice(VERIFIER_NOTES_APPROVED) if status == "approved"
                    else random.choice(VERIFIER_NOTES_REJECTED) if status == "rejected"
                    else ""
                ),
                "created_at": past_iso(created_days_ago),
                "approved_at": past_iso(random.randint(1, created_days_ago)) if status == "approved" else None,
            }
            await db.activities.insert_one(act)
            all_activities.append(act)

            # Update farmer trees
            await db.farmers.update_one(
                {"farmer_id": farmer["farmer_id"]},
                {"$inc": {"total_trees": tree_count}}
            )
            if status == "approved":
                await db.farmers.update_one(
                    {"farmer_id": farmer["farmer_id"]},
                    {"$inc": {
                        "approved_trees": tree_count,
                        "estimated_credits": est_credits,
                        "total_payout": est_payout,
                    }}
                )

    approved = [a for a in all_activities if a["status"] == "approved"]
    pending = [a for a in all_activities if a["status"] == "pending"]
    rejected = [a for a in all_activities if a["status"] == "rejected"]
    print(f"  Created {len(all_activities)} activities: {len(approved)} approved, {len(pending)} pending, {len(rejected)} rejected.")

    # ── 6. Create Ledger Entries ───────────────────────────────
    print("\nCreating ledger entries...")
    ledger_count = 0

    for farmer in all_farmers:
        f_approved = [a for a in all_activities if a["farmer_id"] == farmer["farmer_id"] and a["status"] == "approved"]
        if not f_approved:
            continue
        total_trees = sum(a["tree_count"] for a in f_approved)
        total_credits = round(sum(a["estimated_credits"] for a in f_approved), 4)
        total_payout = round(sum(a["estimated_payout"] for a in f_approved), 2)
        paid_amount = round(total_payout * random.uniform(0.0, 0.6), 2) if random.random() > 0.5 else 0.0

        await db.ledger.insert_one({
            "ledger_id": f"ledger_{uuid.uuid4().hex[:10]}",
            "farmer_id": farmer["farmer_id"],
            "farmer_name": farmer["name"],
            "farmer_phone": farmer["phone"],
            "upi_id": farmer.get("upi_id", ""),
            "project_id": farmer["project_id"],
            "project_name": farmer["project_name"],
            "approved_trees_total": total_trees,
            "approved_credits_total": total_credits,
            "payable_amount": total_payout,
            "paid_amount": paid_amount,
            "updated_at": now_iso(),
        })
        ledger_count += 1

    print(f"  Created {ledger_count} ledger entries.")

    # ── 7. Create Credits (lifecycle demo data) ────────────────
    print("\nCreating credit issuances...")

    # One credit per project in different lifecycle stages
    credit_configs = [
        {
            "project_id": "proj_coastal_001",
            "registry_name": "Verra VCS",
            "credits_issued": 18.75,
            "issuance_date": date_str(60),
            "vintage_year": 2025,
            "registry_reference": "VCS-2025-EG-0042",
            "serial_numbers": "VCU-0042-001 to VCU-0042-018",
            "notes": "First issuance batch for Coastal Green Belt Initiative.",
            "status": "sold",
            "approved_date": date_str(50),
            "buyer_name": "TataConsultancy ESG Fund",
            "sale_price_per_credit": 850.0,
            "sale_date": date_str(35),
            "sale_currency": "INR",
            "total_revenue": 18.75 * 850.0,
        },
        {
            "project_id": "proj_krishna_002",
            "registry_name": "Gold Standard",
            "credits_issued": 24.30,
            "issuance_date": date_str(45),
            "vintage_year": 2025,
            "registry_reference": "GS-VER-2025-KR-017",
            "serial_numbers": "GS-0017-001 to GS-0017-024",
            "notes": "Riparian afforestation first issuance.",
            "status": "approved",
            "approved_date": date_str(30),
            "buyer_name": None,
            "sale_price_per_credit": None,
            "sale_date": None,
            "sale_currency": "INR",
            "total_revenue": None,
        },
        {
            "project_id": "proj_guntur_003",
            "registry_name": "India Carbon Market",
            "credits_issued": 12.60,
            "issuance_date": date_str(25),
            "vintage_year": 2025,
            "registry_reference": "ICM-2025-GNT-009",
            "serial_numbers": "ACC-009-001 to ACC-009-012",
            "notes": "Dryland agroforestry accreditation batch.",
            "status": "issued",
            "approved_date": None,
            "buyer_name": None,
            "sale_price_per_credit": None,
            "sale_date": None,
            "sale_currency": "INR",
            "total_revenue": None,
        },
        {
            "project_id": "proj_vizag_004",
            "registry_name": "Verra VCS",
            "credits_issued": 9.45,
            "issuance_date": date_str(80),
            "vintage_year": 2024,
            "registry_reference": "VCS-2024-VZ-0031",
            "serial_numbers": "VCU-0031-001 to VCU-0031-009",
            "notes": "Pilot batch for tribal forestry program, fully retired.",
            "status": "retired",
            "approved_date": date_str(70),
            "buyer_name": "Infosys Foundation Carbon Neutral",
            "sale_price_per_credit": 920.0,
            "sale_date": date_str(55),
            "sale_currency": "INR",
            "total_revenue": 9.45 * 920.0,
            "retired_date": date_str(20),
            "retirement_reason": "voluntary",
            "retirement_beneficiary": "Infosys Foundation",
        },
    ]

    created_credits = []
    for cc in credit_configs:
        proj = next(p for p in PROJECTS if p["project_id"] == cc["project_id"])
        credit_id = f"credit_{uuid.uuid4().hex[:10]}"
        doc = {
            "credit_id": credit_id,
            "project_id": cc["project_id"],
            "project_name": proj["name"],
            "user_id": user_id,
            "registry_name": cc["registry_name"],
            "credits_issued": cc["credits_issued"],
            "issuance_date": cc["issuance_date"],
            "vintage_year": cc["vintage_year"],
            "registry_reference": cc["registry_reference"],
            "serial_numbers": cc["serial_numbers"],
            "notes": cc["notes"],
            "status": cc["status"],
            "approved_date": cc.get("approved_date"),
            "buyer_name": cc.get("buyer_name"),
            "sale_price_per_credit": cc.get("sale_price_per_credit"),
            "total_revenue": cc.get("total_revenue"),
            "sale_date": cc.get("sale_date"),
            "sale_currency": cc.get("sale_currency", "INR"),
            "retired_date": cc.get("retired_date"),
            "retirement_reason": cc.get("retirement_reason"),
            "retirement_beneficiary": cc.get("retirement_beneficiary"),
            "created_at": cc["issuance_date"] + "T00:00:00+00:00",
            "updated_at": now_iso(),
        }
        await db.credits.insert_one(doc)
        created_credits.append(doc)
        print(f"  + {proj['name']} ({cc['status']}) — {cc['credits_issued']} tCO₂e")

    # ── 8. Create Benefit Shares for sold/retired credits ──────
    print("\nCreating benefit shares for sold/retired credits...")
    bs_count = 0

    for credit in created_credits:
        if credit["status"] not in ("sold", "retired"):
            continue

        total_revenue = credit.get("total_revenue") or 0
        proj_id = credit["project_id"]

        # Get verified activities for this project
        proj_activities = [a for a in all_activities if a["project_id"] == proj_id and a["status"] == "approved"]
        if not proj_activities:
            continue

        total_trees = sum(a["tree_count"] for a in proj_activities)
        if total_trees == 0:
            continue

        # Aggregate per farmer
        farmer_trees = {}
        for act in proj_activities:
            fid = act["farmer_id"]
            farmer_trees[fid] = farmer_trees.get(fid, 0) + act["tree_count"]

        for farmer_id, trees in farmer_trees.items():
            farmer = next((f for f in all_farmers if f["farmer_id"] == farmer_id), None)
            if not farmer:
                continue
            share_pct = round(trees / total_trees, 4)
            rev_share = round(total_revenue * share_pct, 2)

            await db.benefit_shares.insert_one({
                "share_id": f"share_{uuid.uuid4().hex[:10]}",
                "credit_id": credit["credit_id"],
                "project_id": proj_id,
                "farmer_id": farmer_id,
                "farmer_name": farmer["name"],
                "share_percentage": share_pct,
                "trees_contributed": trees,
                "total_project_trees": total_trees,
                "revenue_share": rev_share,
                "currency": credit.get("sale_currency", "INR"),
                "created_at": credit.get("sale_date") or now_iso(),
            })
            bs_count += 1

    print(f"  Created {bs_count} benefit share records.")

    # ── 9. Summary ─────────────────────────────────────────────
    total_approved_trees = sum(a["tree_count"] for a in all_activities if a["status"] == "approved")
    total_credits_est = round(sum(a["estimated_credits"] for a in all_activities if a["status"] == "approved"), 4)
    total_payout_est = round(sum(a["estimated_payout"] for a in all_activities if a["status"] == "approved"), 2)

    print("\n" + "=" * 55)
    print("SEEDING COMPLETE")
    print("=" * 55)
    print(f"  Projects   : {len(PROJECTS)}")
    print(f"  Farmers    : {len(all_farmers)}")
    print(f"  Activities : {len(all_activities)} ({len(approved)} approved, {len(pending)} pending, {len(rejected)} rejected)")
    print(f"  Ledger     : {ledger_count} entries")
    print(f"  Credits    : {len(created_credits)} issuances")
    print(f"  Ben.Shares : {bs_count} records")
    print(f"\n  Approved trees : {total_approved_trees:,}")
    print(f"  Est. credits   : {total_credits_est} tCO2e")
    print(f"  Est. payout    : INR {total_payout_est:,.2f}")
    print("=" * 55)

    client.close()


if __name__ == "__main__":
    asyncio.run(run())
