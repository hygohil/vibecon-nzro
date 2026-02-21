"""
Validate seeded data
Checks data integrity and relationships
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


async def validate_data():
    """Validate database integrity"""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("\n🔍 VALIDATING SEEDED DATA")
    print("="*60)
    
    issues = []
    
    # Check 1: All farmers have valid programs
    print("\n✓ Checking farmer-program relationships...")
    farmers = await db.farmers.find({}, {"_id": 0, "farmer_id": 1, "program_id": 1, "name": 1}).to_list(1000)
    program_ids = set([p["program_id"] for p in await db.programs.find({}, {"_id": 0, "program_id": 1}).to_list(1000)])
    
    orphaned_farmers = 0
    for farmer in farmers:
        if farmer["program_id"] not in program_ids:
            issues.append(f"❌ Farmer {farmer['name']} references non-existent program {farmer['program_id']}")
            orphaned_farmers += 1
    
    if orphaned_farmers == 0:
        print(f"   ✅ All {len(farmers)} farmers have valid programs")
    else:
        print(f"   ⚠️  Found {orphaned_farmers} orphaned farmers")
    
    # Check 2: All claims have valid farmers and programs
    print("\n✓ Checking claim relationships...")
    claims = await db.claims.find({}, {"_id": 0, "claim_id": 1, "farmer_id": 1, "program_id": 1}).to_list(1000)
    farmer_ids = set([f["farmer_id"] for f in farmers])
    
    orphaned_claims = 0
    for claim in claims:
        if claim["farmer_id"] not in farmer_ids:
            issues.append(f"❌ Claim {claim['claim_id']} references non-existent farmer {claim['farmer_id']}")
            orphaned_claims += 1
        if claim["program_id"] not in program_ids:
            issues.append(f"❌ Claim {claim['claim_id']} references non-existent program {claim['program_id']}")
            orphaned_claims += 1
    
    if orphaned_claims == 0:
        print(f"   ✅ All {len(claims)} claims have valid relationships")
    else:
        print(f"   ⚠️  Found {orphaned_claims} orphaned claims")
    
    # Check 3: Ledger entries match approved claims
    print("\n✓ Checking ledger accuracy...")
    ledger_entries = await db.ledger.find({}, {"_id": 0}).to_list(1000)
    
    ledger_mismatches = 0
    for ledger in ledger_entries:
        farmer_id = ledger["farmer_id"]
        
        # Get all approved claims for this farmer
        approved_claims = await db.claims.find(
            {"farmer_id": farmer_id, "status": "approved"},
            {"_id": 0, "tree_count": 1, "estimated_credits": 1, "estimated_payout": 1}
        ).to_list(1000)
        
        actual_trees = sum(c["tree_count"] for c in approved_claims)
        actual_credits = sum(c["estimated_credits"] for c in approved_claims)
        actual_payout = sum(c["estimated_payout"] for c in approved_claims)
        
        # Allow for small rounding differences
        if abs(ledger["approved_trees_total"] - actual_trees) > 0:
            issues.append(f"❌ Ledger mismatch for farmer {farmer_id}: trees {ledger['approved_trees_total']} vs {actual_trees}")
            ledger_mismatches += 1
        
        if abs(ledger["approved_credits_total"] - actual_credits) > 0.01:
            issues.append(f"❌ Ledger mismatch for farmer {farmer_id}: credits {ledger['approved_credits_total']} vs {actual_credits}")
            ledger_mismatches += 1
        
        if abs(ledger["payable_amount"] - actual_payout) > 0.01:
            issues.append(f"❌ Ledger mismatch for farmer {farmer_id}: payout {ledger['payable_amount']} vs {actual_payout}")
            ledger_mismatches += 1
    
    if ledger_mismatches == 0:
        print(f"   ✅ All {len(ledger_entries)} ledger entries are accurate")
    else:
        print(f"   ⚠️  Found {ledger_mismatches} ledger mismatches")
    
    # Check 4: Farmer totals match claims
    print("\n✓ Checking farmer statistics...")
    farmer_stat_errors = 0
    
    for farmer in farmers:
        farmer_claims = await db.claims.find(
            {"farmer_id": farmer["farmer_id"]},
            {"_id": 0, "tree_count": 1, "status": 1, "estimated_credits": 1, "estimated_payout": 1}
        ).to_list(1000)
        
        total_trees = sum(c["tree_count"] for c in farmer_claims)
        approved_trees = sum(c["tree_count"] for c in farmer_claims if c["status"] == "approved")
        
        farmer_doc = await db.farmers.find_one({"farmer_id": farmer["farmer_id"]}, {"_id": 0})
        
        if farmer_doc["total_trees"] != total_trees:
            issues.append(f"❌ Farmer {farmer_doc['name']}: total_trees {farmer_doc['total_trees']} vs {total_trees}")
            farmer_stat_errors += 1
        
        if farmer_doc["approved_trees"] != approved_trees:
            issues.append(f"❌ Farmer {farmer_doc['name']}: approved_trees {farmer_doc['approved_trees']} vs {approved_trees}")
            farmer_stat_errors += 1
    
    if farmer_stat_errors == 0:
        print(f"   ✅ All farmer statistics are correct")
    else:
        print(f"   ⚠️  Found {farmer_stat_errors} farmer statistic errors")
    
    # Check 5: Data completeness
    print("\n✓ Checking data completeness...")
    incomplete = 0
    
    # Check for farmers without UPI
    no_upi = await db.farmers.count_documents({"$or": [{"upi_id": None}, {"upi_id": ""}]})
    if no_upi > 0:
        print(f"   ⚠️  {no_upi} farmers without UPI ID")
        incomplete += 1
    
    # Check for claims without photos
    no_photos = await db.claims.count_documents({"photo_urls": {"$size": 0}})
    if no_photos > 0:
        print(f"   ⚠️  {no_photos} claims without photos")
        incomplete += 1
    
    # Check for claims without location
    no_location = await db.claims.count_documents({"$or": [{"lat": None}, {"lng": None}]})
    if no_location > 0:
        print(f"   ⚠️  {no_location} claims without location")
        incomplete += 1
    
    if incomplete == 0:
        print(f"   ✅ All records have required data")
    
    # Check 6: Carbon calculation accuracy
    print("\n✓ Validating carbon calculations...")
    
    SPECIES_RATES = {
        "fast_growing": 0.02,
        "medium": 0.01,
        "slow": 0.005
    }
    
    def get_species_bucket(species_name: str) -> str:
        fast = ["eucalyptus", "bamboo", "poplar", "moringa", "subabul"]
        medium = ["neem", "mango", "teak", "banyan", "peepal", "jackfruit"]
        lower = species_name.lower().strip()
        if lower in fast:
            return "fast_growing"
        elif lower in medium:
            return "medium"
        return "slow"
    
    calc_errors = 0
    for claim in claims[:50]:  # Sample check
        claim_full = await db.claims.find_one({"claim_id": claim["claim_id"]}, {"_id": 0})
        program = await db.programs.find_one({"program_id": claim["program_id"]}, {"_id": 0})
        
        if program:
            bucket = get_species_bucket(claim_full["species"])
            rate = SPECIES_RATES.get(bucket, 0.01)
            survival = program.get("survival_rate", 0.7)
            discount = program.get("conservative_discount", 0.2)
            
            expected_credits = round(claim_full["tree_count"] * rate * survival * (1 - discount), 4)
            
            if abs(claim_full["estimated_credits"] - expected_credits) > 0.01:
                issues.append(f"❌ Claim {claim['claim_id']}: credits calculation mismatch")
                calc_errors += 1
    
    if calc_errors == 0:
        print(f"   ✅ Carbon calculations are correct (sampled 50 claims)")
    else:
        print(f"   ⚠️  Found {calc_errors} calculation errors")
    
    # Final summary
    print("\n" + "="*60)
    if len(issues) == 0:
        print("✅ VALIDATION PASSED - No issues found!")
    else:
        print(f"⚠️  VALIDATION COMPLETED - Found {len(issues)} issues")
        print("\nFirst 10 issues:")
        for issue in issues[:10]:
            print(f"  {issue}")
        if len(issues) > 10:
            print(f"\n  ... and {len(issues) - 10} more issues")
    
    print("="*60 + "\n")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(validate_data())
