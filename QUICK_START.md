# Aggregator OS - Quick Start Guide

## 🚀 Quick Commands

### Database Seeding

All commands run from `/app/backend/`:

```bash
# Using CLI Tool (Recommended)
python3 db_seed.py seed      # Populate database with test data
python3 db_seed.py stats     # View what's in the database
python3 db_seed.py validate  # Check data integrity
python3 db_seed.py clear     # Remove all seed data
python3 db_seed.py reset     # Clear + re-seed fresh
python3 db_seed.py help      # See all options
```

### What You Get After Seeding

✅ **4 Programs** - Different regions and tree species
✅ **65 Farmers** - With realistic Indian data (names, villages, phone, UPI)
✅ **~220 Claims** - Mix of approved, pending, and rejected
✅ **60 Ledger Entries** - Payout calculations ready
✅ **~12,000 Trees** - Spread across programs
✅ **~84 tCO₂e Credits** - Estimated carbon sequestration
✅ **~₹530,000 Payout** - Ready for testing

### Development Workflow

```bash
# 1. First time setup
cd /app/backend
python3 db_seed.py seed

# 2. Check what's in the database
python3 db_seed.py stats

# 3. Develop your feature...

# 4. Need fresh data?
python3 db_seed.py reset

# 5. Validate everything is correct
python3 db_seed.py validate
```

### Testing the Application

**Backend API Testing:**
```bash
# Get backend URL
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)

# Test endpoints (after login)
curl "$API_URL/api/programs" -H "Cookie: session_token=TOKEN"
curl "$API_URL/api/farmers" -H "Cookie: session_token=TOKEN"
curl "$API_URL/api/claims?status=pending" -H "Cookie: session_token=TOKEN"
```

**Frontend Testing:**
1. Login with Google OAuth
2. Visit pages:
   - Dashboard → See metrics
   - Programs → 11 total programs
   - Farmers → 136 farmers
   - Claims → 71 pending claims
   - Ledger → 123 payout entries
   - Exports → Generate CSVs/PDFs

### Service Management

```bash
# Check status
sudo supervisorctl status

# Restart services
sudo supervisorctl restart frontend
sudo supervisorctl restart backend

# View logs
tail -f /var/log/supervisor/backend.out.log
tail -f /var/log/supervisor/frontend.out.log
```

### File Locations

**Backend:**
- `/app/backend/server.py` - Main API
- `/app/backend/db_seed.py` - Seeding CLI
- `/app/backend/.env` - Environment variables

**Frontend:**
- `/app/frontend/src/pages/` - All pages
- `/app/frontend/src/components/ui/` - UI components
- `/app/frontend/.env` - Frontend config

**Documentation:**
- `/app/memory/PRD.md` - Product requirements
- `/app/backend/SEEDING_README.md` - Detailed seeding guide
- `/app/UI_ENHANCEMENTS.md` - UI improvements guide
- `/app/QUICK_START.md` - This file

### Common Tasks

**Add a new program:**
```bash
# Via UI: Programs page → Create Program
# Select region from dropdown (searchable)
# All 36 Indian states/UTs available
```

**Add a farmer:**
```bash
# Via UI: Farmers page → Add Farmer
# Phone input has country code selector (🇮🇳 +91 default)
# 26 countries supported
```

**Approve a claim:**
```bash
# Via UI: Claims page → Click pending claim → Approve
# Automatically updates ledger and farmer stats
```

**Export data:**
```bash
# Via UI: Exports page
# 5 types: PDF Dossier, Activity CSV, Evidence JSON, Calculation Sheet, Audit Log
```

### UI Features

**✨ New Components:**
- **Searchable Region Dropdown** - Type to find Indian states
- **Phone Input with Country Code** - Visual flags, 26 countries

**📁 Components Location:**
- `/app/frontend/src/components/ui/combobox.jsx`
- `/app/frontend/src/components/ui/phone-input.jsx`
- `/app/frontend/src/lib/indian-states.js`

### Environment Variables

**Backend (.env):**
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
CORS_ORIGINS=*
```

**Frontend (.env):**
```
REACT_APP_BACKEND_URL=https://vanaledger-refactor.preview.emergentagent.com
```

**⚠️ IMPORTANT:** Never hardcode these values in code. Always use environment variables.

### Troubleshooting

**Issue: Backend not responding**
```bash
sudo supervisorctl restart backend
tail -f /var/log/supervisor/backend.err.log
```

**Issue: Frontend not loading**
```bash
sudo supervisorctl restart frontend
tail -f /var/log/supervisor/frontend.err.log
```

**Issue: Database empty after seeding**
```bash
# Check if MongoDB is running
sudo supervisorctl status mongodb

# Re-run seeder
cd /app/backend && python3 db_seed.py reset
```

**Issue: Need to clear all data**
```bash
cd /app/backend && python3 db_seed.py clear
```

### Next Steps

1. ✅ Database is seeded
2. ✅ UI enhancements are live
3. 🔄 Test the application
4. 🚀 Build new features

For detailed documentation:
- Database Seeding: `/app/backend/SEEDING_README.md`
- UI Components: `/app/UI_ENHANCEMENTS.md`
- Product Roadmap: `/app/memory/PRD.md`

---

**Need Help?**
- Check logs: `/var/log/supervisor/*.log`
- View database stats: `python3 db_seed.py stats`
- Validate data: `python3 db_seed.py validate`
- Reset everything: `python3 db_seed.py reset`

**Happy coding! 🌳**
