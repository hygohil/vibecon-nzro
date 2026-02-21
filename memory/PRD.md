# VanaLedger - Aggregator OS for Carbon Credit Tree Plantation

## Original Problem Statement
Build an Aggregator OS + WhatsApp farmer onboarding + tree-plantation ledger + payout calculator for carbon credit management. Two personas: Aggregator (Web panel) and Farmer (WhatsApp, external). Core flows: Program creation, Farmer onboarding, Claim submission with geo+photo evidence, Aggregator verification, Payout ledger, and comprehensive MRV-ready exports.

## Architecture
- **Frontend**: React 19 + Tailwind CSS + Shadcn/UI components
- **Backend**: FastAPI (Python) on port 8001
- **Database**: MongoDB (Motor async driver)
- **Auth**: Emergent-managed Google OAuth
- **Design**: "Agro-Trust" theme - Forest Canopy (#1A4D2E) + Terracotta (#B45309)

## User Personas
1. **Aggregator** - Carbon credit program manager using web dashboard
2. **Farmer** - Enrolled via WhatsApp (external platform), interacts through webhook APIs

## Core Requirements
- Google OAuth authentication for aggregators
- CRUD for tree plantation programs with configurable parameters
- Farmer management (onboarding, tracking)
- Claims queue with evidence review (photos + geo coordinates)
- Carbon credit estimation (rule-of-thumb: tree_count x rate x survival x (1-discount))
- Payout ledger with farmer-wise balance tracking
- 5 export types: PDF Dossier, Activity CSV, Evidence JSON, Calculation Sheet, Audit Log
- WhatsApp webhook endpoints (JOIN, CLAIM, STATUS)

## What's Been Implemented (Feb 21, 2026)
- [x] Emergent Google OAuth login with session management
- [x] Dashboard with bento grid metrics (8 KPIs)
- [x] Programs CRUD (create/view/delete with species, rates, fraud controls)
- [x] Farmers CRUD (add/list/search/filter by program)
- [x] Claims queue (submit/approve/reject/needs-info with evidence viewer)
- [x] Payout ledger (auto-updates on approval, farmer-wise balance, CSV export)
- [x] Export Center: PDF Dossier, Activity CSV, Evidence JSON, Calculation Sheet, Audit Log
- [x] WhatsApp webhook endpoints: /api/webhook/join, /api/webhook/claim, /api/webhook/status
- [x] Carbon credit estimation formula with configurable species buckets
- [x] Sidebar navigation with collapse/expand
- [x] "Estimated units - not issued credits" disclaimers throughout

## Prioritized Backlog
### P0 (Critical)
- All P0 features implemented

### P1 (High Priority)
- Map view with Leaflet pins for geo-evidence visualization
- Duplicate claim detection (same location + similar timeframe)
- WhatsApp reminder scheduling (30/90/365 day survival checks)
- Legal & Rights Pack PDF export (consent, rights assignment, non-duplication)
- ZIP evidence pack export (bundled photos + geo data + logs)

### P2 (Medium Priority)
- Farmer consent/participation agreement capture
- Photo hash-based duplicate detection
- Bulk claim approval/rejection
- UPI payout integration
- Program-level analytics with charts (Recharts)
- Farmer profile detail view with claim history

### P3 (Nice to Have)
- Multi-language support (Hindi, Gujarati)
- Push notifications for claim status changes
- Nursery invoice capture
- Field visit scheduling
- Carbon price market data integration

## Database Seeding & Testing

### Quick Commands
All seeding operations can be run from `/app/backend/`:

```bash
# Main CLI tool (recommended)
python3 db_seed.py [command]

# Available commands:
python3 db_seed.py seed       # Seed database with test data
python3 db_seed.py clear      # Clear all seed data
python3 db_seed.py stats      # View database statistics
python3 db_seed.py validate   # Validate data integrity
python3 db_seed.py reset      # Clear + re-seed (fresh start)
python3 db_seed.py help       # Show all options

# Alternative: Direct scripts
python3 seed_data.py          # Run seeder directly
python3 view_db_stats.py      # View statistics
python3 validate_seed_data.py # Validate data
python3 clear_seed_data.py    # Clear data
```

### What Gets Seeded

**4 Tree Plantation Programs:**
- Coastal Green Belt Initiative (East Godavari) - Neem, Eucalyptus, Coconut
- Krishna River Basin Afforestation (Krishna) - Bamboo, Banyan, Peepal
- Guntur Dryland Agroforestry (Guntur) - Moringa, Neem, Mango
- Urban Fringe Carbon Sequestration (Guntur) - Teak, Sandalwood

**65 Farmers:** Realistic Indian names, villages, phone numbers (+91), UPI IDs

**~220 Claims:** 60% approved, 15% pending, 25% rejected
- Geo-tagged locations (Andhra Pradesh coordinates)
- Sample photos (Unsplash URLs)
- 12 tree species mix
- Carbon calculations applied

**60 Ledger Entries:** Auto-generated for farmers with approved claims

### Test Data Summary
- 🌳 ~12,000 approved trees per run
- 🌍 ~84 tCO₂e estimated credits
- 💵 ~₹530,000 total payout
- 📍 30 villages across 5 districts
- 🌱 12 tree species (fast/medium/slow growing)

### Seeding Scripts Location
`/app/backend/`:
- `db_seed.py` - Main CLI tool (NEW)
- `seed_data.py` - Core seeding logic
- `view_db_stats.py` - Statistics viewer
- `validate_seed_data.py` - Data integrity checker
- `clear_seed_data.py` - Data cleanup
- `SEEDING_README.md` - Full documentation
- `SEEDING_SUMMARY.md` - Quick reference

### When to Use
- **Development:** Seed once at project start
- **Testing:** Reset before major feature tests
- **Demo:** Re-seed for clean demo data
- **CI/CD:** Automate seeding in test environments

## Next Tasks
1. Add Leaflet map view for claims geo-evidence
2. Implement Legal & Rights Pack PDF export
3. Add ZIP evidence pack export
4. Build duplicate claim detection
5. Add survival check reminder scheduling
