# Database Seeding Scripts

This directory contains scripts to populate your Aggregator OS database with realistic test data.

## 📁 Available Scripts

### 1. `seed_data.py` - Create Test Data
Creates comprehensive test data including:
- **4 Tree Plantation Programs** across different regions (East Godavari, Krishna, Guntur)
- **65 Farmers** with realistic Indian names, villages, and contact details
- **~220 Claims** with varied statuses (approved, pending, rejected)
- **Ledger entries** for farmers with approved claims
- **Realistic data**: Geo-coordinates, tree species, carbon calculations, photo URLs

**Usage:**
```bash
cd /app/backend
python3 seed_data.py

# Or use the shell script
./seed.sh
```

**What it creates:**
- Programs with different payout models (per_tree, per_credit)
- Multiple tree species (neem, mango, eucalyptus, bamboo, etc.)
- Claims with geo-tagged locations in Andhra Pradesh
- Sample photos from Unsplash
- Carbon credit calculations using the configured formula
- Ledger entries with partial payments for some farmers

---

### 2. `view_db_stats.py` - View Database Statistics
Displays current database statistics and sample data.

**Usage:**
```bash
cd /app/backend
python3 view_db_stats.py
```

**Shows:**
- Total counts for all collections
- Claims breakdown by status
- Aggregated totals (trees, credits, payouts)
- Sample programs and farmers

---

### 3. `clear_seed_data.py` - Clear All Seed Data
⚠️ **WARNING**: Deletes all programs, farmers, claims, and ledger entries.
User accounts and sessions are preserved.

**Usage:**
```bash
cd /app/backend
python3 clear_seed_data.py
```

---

## 🌍 Sample Data Details

### Programs Created
1. **Coastal Green Belt Initiative** (East Godavari)
   - Species: Neem, Eucalyptus, Coconut
   - Payout: ₹50/tree
   - 75% survival rate

2. **Krishna River Basin Afforestation** (Krishna)
   - Species: Bamboo, Banyan, Peepal, Tamarind
   - Payout: ₹60/tree
   - 70% survival rate

3. **Guntur Dryland Agroforestry** (Guntur)
   - Species: Moringa, Neem, Mango, Jackfruit
   - Payout: ₹45/tree
   - 65% survival rate

4. **Urban Fringe Carbon Sequestration** (Guntur)
   - Species: Teak, Sandalwood, Eucalyptus
   - Payout: ₹500/tCO₂e (per credit model)
   - 80% survival rate

### Tree Species with Carbon Rates
| Species | Growth Rate | Carbon Rate (tCO₂/tree/year) |
|---------|-------------|------------------------------|
| Eucalyptus, Bamboo, Moringa | Fast | 0.02 |
| Neem, Mango, Teak, Banyan, Peepal | Medium | 0.01 |
| Tamarind, Coconut, Sandalwood | Slow | 0.005 |

### Geographic Coverage
- **Districts**: Krishna, Guntur, Prakasam, East Godavari, West Godavari
- **Villages**: 30 different villages across Andhra Pradesh
- **Coordinates**: Realistic lat/lng for each region

---

## 🔄 Typical Workflow

### Fresh Start
```bash
# 1. Clear existing data (optional)
python3 clear_seed_data.py

# 2. Seed new data
python3 seed_data.py

# 3. View stats
python3 view_db_stats.py
```

### Re-seed Without Clearing
The seed script is **idempotent-friendly**. If you want to add more data without clearing, just run:
```bash
python3 seed_data.py
```

Note: The commented-out lines in `seed_data.py` can be uncommented to clear data before seeding.

---

## 📊 Expected Output

After seeding, you should have approximately:
- **4 programs**
- **65 farmers**
- **220 claims** (60% approved, 15% pending, 25% rejected)
- **60 ledger entries** (only for farmers with approved claims)
- **~12,000+ trees** (approved)
- **~85 tCO₂e** estimated credits
- **~₹540,000** total payout

---

## 🧪 Testing the Data

### Via API (using curl)
```bash
# Get backend URL
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)

# Login first (get session token)
# Then test endpoints:

# View programs
curl "$API_URL/api/programs" -H "Cookie: session_token=YOUR_TOKEN"

# View farmers
curl "$API_URL/api/farmers" -H "Cookie: session_token=YOUR_TOKEN"

# View pending claims
curl "$API_URL/api/claims?status=pending" -H "Cookie: session_token=YOUR_TOKEN"

# View ledger
curl "$API_URL/api/ledger" -H "Cookie: session_token=YOUR_TOKEN"
```

### Via Frontend
1. Login with Google OAuth
2. Navigate to different pages:
   - Dashboard: See overview statistics
   - Programs: View all 4 programs
   - Farmers: Browse 65 farmers
   - Claims: Review pending claims
   - Ledger: Check payout ledger

---

## 🎯 Customization

### Modify Seed Data
Edit `seed_data.py` to customize:

**Add more programs:**
```python
programs_data.append({
    "name": "Your Program Name",
    "region": "Your Region",
    # ... other fields
})
```

**Change farmer count:**
```python
farmers_per_program = [20, 30, 25, 15]  # Modify these numbers
```

**Adjust claim ratios:**
```python
claim_statuses = ["approved", "approved", "pending", "rejected"]  # 50% approved
```

**Add new villages/districts:**
```python
INDIAN_VILLAGES.append("Your Village Name")
DISTRICTS.append("Your District")
```

---

## 🔍 Debugging

If seeding fails:

1. **Check MongoDB connection:**
   ```bash
   mongo --eval "db.adminCommand('ping')"
   ```

2. **Verify environment variables:**
   ```bash
   cat /app/backend/.env
   ```

3. **Check for errors:**
   ```bash
   python3 seed_data.py 2>&1 | tee seed_log.txt
   ```

4. **Manually inspect database:**
   ```bash
   mongo
   use test_database
   db.programs.find().pretty()
   ```

---

## 📝 Notes

- **User Requirement**: The script requires at least one user in the database. If no user exists, it creates a test user.
- **Photo URLs**: Uses Unsplash images via direct URLs (royalty-free)
- **Phone Numbers**: Random Indian phone numbers (+91 prefix)
- **UPI IDs**: Random but realistic format (name123@paytm)
- **Coordinates**: Realistic lat/lng for Andhra Pradesh regions
- **Dates**: Randomized within realistic ranges (last 30-180 days)

---

## 🚀 Production Considerations

**DO NOT run these scripts in production!**

These scripts are for development and testing only. In production:
- Use proper data migration tools
- Implement proper validation
- Use real farmer data from your onboarding flow
- Implement proper backup before any data operations
