# Aggregator OS - Command Reference

## 📋 All Available Commands

### Database Seeding (Primary Tool)

**Location:** `/app/backend/`

```bash
# Main CLI - One tool for everything
python3 db_seed.py seed      # Seed database with test data
python3 db_seed.py clear     # Clear all seed data  
python3 db_seed.py stats     # View database statistics
python3 db_seed.py validate  # Validate data integrity
python3 db_seed.py reset     # Clear + re-seed (fresh start)
python3 db_seed.py help      # Show help and options
```

**What Each Command Does:**

| Command | Description | Use When |
|---------|-------------|----------|
| `seed` | Adds 4 programs, 65 farmers, ~220 claims | Starting development or need more test data |
| `clear` | Removes all programs, farmers, claims, ledger | Want to clean database (keeps users) |
| `stats` | Shows counts, totals, sample data | Checking what's in database |
| `validate` | Checks data integrity, relationships | After manual changes or debugging |
| `reset` | Runs clear then seed | Want fresh start with clean data |

---

### Alternative: Direct Scripts

If you prefer running individual scripts:

```bash
cd /app/backend

# Seeding
python3 seed_data.py          # Same as: db_seed.py seed
python3 clear_seed_data.py    # Same as: db_seed.py clear
python3 view_db_stats.py      # Same as: db_seed.py stats
python3 validate_seed_data.py # Same as: db_seed.py validate

# Interactive menu
./seed_menu.sh                # Shows menu with options
```

---

## 📁 File Reference

### Seeding & Database

| File | Purpose | When to Use |
|------|---------|-------------|
| `/app/backend/db_seed.py` | **Main CLI tool** | All seeding operations |
| `/app/backend/seed_data.py` | Core seeding logic | Advanced: custom seeding |
| `/app/backend/clear_seed_data.py` | Data cleanup | When you need to clear data |
| `/app/backend/view_db_stats.py` | Statistics viewer | Check database state |
| `/app/backend/validate_seed_data.py` | Data validator | Verify data integrity |
| `/app/backend/seed_menu.sh` | Interactive menu | GUI-like interface |

### Documentation

| File | Content | Read When |
|------|---------|-----------|
| `/app/QUICK_START.md` | **Quick start guide** | First time setup |
| `/app/backend/SEEDING_README.md` | Detailed seeding docs | Deep dive on seeding |
| `/app/backend/SEEDING_SUMMARY.md` | Seeding summary | Quick reference |
| `/app/UI_ENHANCEMENTS.md` | UI components guide | Using new UI features |
| `/app/memory/PRD.md` | Product requirements | Understanding features |
| `/app/COMMANDS.md` | This file | Finding commands |

### Application Code

| Location | Contains |
|----------|----------|
| `/app/backend/server.py` | Main FastAPI app, all API endpoints |
| `/app/frontend/src/pages/` | All React pages (Dashboard, Programs, etc.) |
| `/app/frontend/src/components/ui/` | Reusable UI components |
| `/app/frontend/src/lib/` | Utility functions, data files |

---

## 🎯 Common Scenarios

### Scenario 1: First Time Setup
```bash
cd /app/backend
python3 db_seed.py seed
python3 db_seed.py stats
```

### Scenario 2: Need Fresh Data
```bash
cd /app/backend
python3 db_seed.py reset
```

### Scenario 3: Check Database State
```bash
cd /app/backend
python3 db_seed.py stats
python3 db_seed.py validate
```

### Scenario 4: Clear Everything
```bash
cd /app/backend
python3 db_seed.py clear
```

### Scenario 5: Testing/Demo Preparation
```bash
cd /app/backend
python3 db_seed.py reset     # Fresh data
python3 db_seed.py validate  # Verify integrity
python3 db_seed.py stats     # Check totals
```

### Scenario 6: Development Workflow
```bash
# Morning: Start fresh
python3 db_seed.py reset

# During dev: Check state
python3 db_seed.py stats

# Before commit: Validate
python3 db_seed.py validate

# End of day: Check totals
python3 db_seed.py stats
```

---

## 🔧 Service Management

### Check Status
```bash
sudo supervisorctl status
```

### Restart Services
```bash
sudo supervisorctl restart frontend
sudo supervisorctl restart backend
sudo supervisorctl restart frontend backend  # Both at once
```

### View Logs
```bash
# Backend logs
tail -f /var/log/supervisor/backend.out.log
tail -f /var/log/supervisor/backend.err.log

# Frontend logs  
tail -f /var/log/supervisor/frontend.out.log
tail -f /var/log/supervisor/frontend.err.log

# Last 50 lines
tail -n 50 /var/log/supervisor/backend.err.log
```

---

## 🧪 API Testing

### Get Backend URL
```bash
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
echo $API_URL
```

### Test Endpoints
```bash
# Public endpoints
curl "$API_URL/api/webhook/status" -X POST \
  -H "Content-Type: application/json" \
  -d '{"phone":"+919876543210"}'

# Authenticated endpoints (need login first)
curl "$API_URL/api/programs" \
  -H "Cookie: session_token=YOUR_TOKEN"

curl "$API_URL/api/farmers" \
  -H "Cookie: session_token=YOUR_TOKEN"

curl "$API_URL/api/claims?status=pending" \
  -H "Cookie: session_token=YOUR_TOKEN"
```

---

## 📊 Data Insights

### After Running `db_seed.py seed`

**You Get:**
- 4 new programs (different regions)
- 65 new farmers (Indian names, villages, UPI)
- ~220 new claims (approved/pending/rejected)
- 60 new ledger entries
- ~12,000 approved trees
- ~84 tCO₂e estimated credits
- ~₹530,000 total payout

**Realistic Data:**
- 30 villages across Andhra Pradesh
- 5 districts (Krishna, Guntur, East Godavari, etc.)
- 12 tree species (Neem, Eucalyptus, Bamboo, etc.)
- Geo-tagged locations (accurate lat/lng)
- Sample photos (Unsplash URLs)
- Phone numbers (+91 prefix)
- UPI IDs (name123@paytm format)

---

## 🚨 Troubleshooting

### Database Empty After Seeding
```bash
# Check MongoDB is running
sudo supervisorctl status mongodb

# Check logs
tail -n 50 /var/log/supervisor/backend.err.log

# Try reset
python3 db_seed.py reset
```

### Services Not Starting
```bash
# Check status
sudo supervisorctl status

# Restart
sudo supervisorctl restart all

# Check logs
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/frontend.err.log
```

### Frontend Not Loading
```bash
# Restart frontend
sudo supervisorctl restart frontend

# Check if building
tail -f /var/log/supervisor/frontend.out.log

# Wait 30 seconds for webpack compilation
```

---

## 🎓 Learning Path

**Day 1:** Start Here
1. Read `/app/QUICK_START.md`
2. Run `python3 db_seed.py seed`
3. Run `python3 db_seed.py stats`
4. Login and explore UI

**Day 2:** Understand Data
1. Read `/app/backend/SEEDING_README.md`
2. Run `python3 db_seed.py validate`
3. Test API endpoints with curl

**Day 3:** Build Features
1. Read `/app/memory/PRD.md`
2. Check `/app/UI_ENHANCEMENTS.md` for components
3. Start development with `python3 db_seed.py reset`

---

## 📝 Quick Reference Card

**Most Used Commands:**
```bash
# Seed database
python3 db_seed.py seed

# Check what's there
python3 db_seed.py stats

# Fresh start
python3 db_seed.py reset

# Verify data
python3 db_seed.py validate

# Clear everything
python3 db_seed.py clear
```

**Service Commands:**
```bash
# Status
sudo supervisorctl status

# Restart
sudo supervisorctl restart frontend backend

# Logs
tail -f /var/log/supervisor/backend.err.log
```

**File Locations:**
```
/app/backend/db_seed.py          # Main seeding tool
/app/backend/server.py           # Backend API
/app/frontend/src/pages/         # Frontend pages
/app/QUICK_START.md              # Quick start
/app/COMMANDS.md                 # This file
```

---

**💡 Pro Tip:** Bookmark this file for quick command reference!

**Last Updated:** Feb 21, 2026
