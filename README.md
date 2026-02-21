# 🌳 Aggregator OS - Tree Plantation Carbon Credit Management

A full-stack application for managing tree plantation programs, farmer onboarding, claim verification, and carbon credit tracking.

## 🚀 Quick Start (30 seconds)

```bash
# 1. Seed the database with test data
cd /app/backend
python3 db_seed.py seed

# 2. Check what was created
python3 db_seed.py stats

# 3. Open the app and login
# Visit: https://your-app.preview.emergentagent.com
```

**That's it!** You now have:
- ✅ 4 programs
- ✅ 65 farmers  
- ✅ ~220 claims
- ✅ 60 ledger entries
- ✅ ~12,000 trees
- ✅ ~₹530,000 in payouts

---

## 📚 Documentation

| Document | Purpose | Start Here |
|----------|---------|------------|
| 🎯 **[QUICK_START.md](QUICK_START.md)** | Get up and running | **← Read this first** |
| 📋 [COMMANDS.md](COMMANDS.md) | All available commands | Quick reference |
| 🌱 [backend/SEEDING_README.md](backend/SEEDING_README.md) | Detailed seeding guide | Deep dive |
| 🎨 [UI_ENHANCEMENTS.md](UI_ENHANCEMENTS.md) | UI components guide | Using new features |
| 📖 [memory/PRD.md](memory/PRD.md) | Product requirements | Understanding app |

---

## 🛠️ Tech Stack

- **Frontend:** React 19 + TailwindCSS + Shadcn UI
- **Backend:** FastAPI (Python) + MongoDB
- **Auth:** Emergent-managed Google OAuth
- **Design:** Agriculture/Sustainability theme

---

## ✨ Key Features

### For Aggregators (Web Dashboard)
- 📋 **Programs:** Create and manage tree plantation programs
- 👨‍🌾 **Farmers:** Onboard and track farmers
- 📝 **Claims:** Review and approve planting claims with photos
- 💰 **Ledger:** Track payouts and balances
- 📊 **Dashboard:** Real-time metrics and KPIs
- 📤 **Exports:** PDF, CSV, JSON reports

### For Farmers (WhatsApp API)
- 🔔 **JOIN:** Enroll in programs
- 🌱 **CLAIM:** Submit tree plantation claims
- 📊 **STATUS:** Check claim status and earnings

---

## 🎯 Main Commands

### Database Operations
```bash
cd /app/backend

python3 db_seed.py seed      # Add test data
python3 db_seed.py stats     # View database statistics  
python3 db_seed.py validate  # Check data integrity
python3 db_seed.py reset     # Fresh start (clear + seed)
python3 db_seed.py clear     # Remove all seed data
```

### Service Management
```bash
sudo supervisorctl status              # Check services
sudo supervisorctl restart frontend    # Restart frontend
sudo supervisorctl restart backend     # Restart backend
```

### View Logs
```bash
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/frontend.out.log
```

---

## 📁 Project Structure

```
/app/
├── backend/
│   ├── server.py              # Main FastAPI app
│   ├── db_seed.py            # Seeding CLI tool ⭐
│   ├── seed_data.py          # Seeding logic
│   ├── .env                  # Backend config
│   └── SEEDING_README.md     # Seeding docs
│
├── frontend/
│   ├── src/
│   │   ├── pages/           # All pages
│   │   ├── components/ui/   # UI components
│   │   └── lib/            # Utilities
│   └── .env                 # Frontend config
│
├── memory/
│   └── PRD.md               # Product requirements
│
├── QUICK_START.md           # Quick start guide ⭐
├── COMMANDS.md              # Command reference ⭐
├── UI_ENHANCEMENTS.md       # UI features
└── README.md                # This file
```

---

## 🎨 UI Features

### Searchable Region Dropdown
- 36 Indian states/UTs
- Type-to-search functionality
- Used in: Programs creation

### Phone Input with Country Code
- 26 countries with flags
- Auto-formatting
- Used in: Farmer creation

---

## 🧪 Testing

### Frontend
1. Login with Google OAuth
2. Navigate through all pages
3. Create programs, add farmers, review claims

### Backend API
```bash
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
curl "$API_URL/api/dashboard/stats" -H "Cookie: session_token=TOKEN"
```

---

## 🔄 Development Workflow

```bash
# Morning: Fresh start
python3 db_seed.py reset

# During development
# ... make changes ...

# Check database state
python3 db_seed.py stats

# Validate changes
python3 db_seed.py validate

# Before commit
python3 db_seed.py validate
```

---

## 🌍 Environment Variables

### Backend (.env)
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
CORS_ORIGINS=*
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=https://your-app.preview.emergentagent.com
```

**⚠️ Important:** Never hardcode these in code!

---

## 🎓 Getting Started

**New to this project?**

1. **Read:** [QUICK_START.md](QUICK_START.md) (5 min read)
2. **Seed:** Run `python3 db_seed.py seed`
3. **Explore:** Login and test all features
4. **Learn:** Read [memory/PRD.md](memory/PRD.md) for full context
5. **Build:** Start adding features!

**Need help?**
- Check [COMMANDS.md](COMMANDS.md) for all commands
- View logs for errors
- Run `python3 db_seed.py validate` to check data

---

## 📊 Sample Data After Seeding

**Programs (4):**
- Coastal Green Belt Initiative (East Godavari)
- Krishna River Basin Afforestation (Krishna)
- Guntur Dryland Agroforestry (Guntur)
- Urban Fringe Carbon Sequestration (Guntur)

**Data Points:**
- 65 farmers with realistic Indian data
- ~220 claims (mix of statuses)
- 30 villages across 5 districts
- 12 tree species
- Geo-tagged locations
- Sample photos

**Metrics:**
- ~12,000 approved trees
- ~84 tCO₂e credits
- ~₹530,000 payouts

---

## 🚨 Troubleshooting

**Database empty?**
```bash
python3 db_seed.py reset
```

**Services not running?**
```bash
sudo supervisorctl restart all
```

**Frontend not loading?**
```bash
sudo supervisorctl restart frontend
# Wait 30 seconds for webpack
```

**Check logs:**
```bash
tail -f /var/log/supervisor/*.log
```

---

## 🎯 Next Steps

1. ✅ Database seeded
2. ✅ UI enhancements live
3. 🔄 Test the application
4. 🚀 Build new features

**Feature Backlog:**
- Map view for geo-evidence
- Duplicate claim detection
- Legal & Rights Pack export
- Survival check reminders

See [memory/PRD.md](memory/PRD.md) for complete roadmap.

---

## 📞 Support

**Documentation:**
- Quick Start: [QUICK_START.md](QUICK_START.md)
- Commands: [COMMANDS.md](COMMANDS.md)
- Seeding: [backend/SEEDING_README.md](backend/SEEDING_README.md)
- UI Guide: [UI_ENHANCEMENTS.md](UI_ENHANCEMENTS.md)

**Debugging:**
- Check service status: `sudo supervisorctl status`
- View logs: `tail -f /var/log/supervisor/*.log`
- Validate data: `python3 db_seed.py validate`

---

**Built with ❤️ for sustainable tree plantation and carbon credit management**

*Last Updated: Feb 21, 2026*
