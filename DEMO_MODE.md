# Demo Mode Feature Documentation

## 🎭 What is Demo Mode?

Demo Mode allows users to explore the Aggregator OS with realistic sample data **without creating an account**. It's perfect for:
- First-time visitors exploring the app
- Product demos and presentations  
- Testing features without affecting real data
- Showing stakeholders what the app can do

---

## ✨ Features

### For Users
- ✅ **No Login Required** - Access instantly via "Try Demo" button
- ✅ **Realistic Data** - 4 programs, 65 farmers, ~220 claims
- ✅ **Full Functionality** - View all pages and features
- ✅ **Safe Environment** - Your real data stays separate
- ✅ **Easy Exit** - Click "Exit Demo" to return to normal mode

### For Developers
- ✅ **Dedicated Demo Account** - Separate demo user in database
- ✅ **Auto-Seeding** - CLI creates demo data automatically
- ✅ **Isolated Data** - Demo data has `demo_` prefix in IDs
- ✅ **Persistent** - Demo account and data survive resets

---

## 🚀 How to Use

### As a User

**Entering Demo Mode:**
1. Go to login page
2. Click "Try Demo Mode" button
3. Instantly see app with sample data

**Exiting Demo Mode:**
1. Click "Exit Demo" button in top banner
2. Returns to normal login flow

**Visual Indicator:**
- Amber banner at top shows "Demo Mode Active"
- Banner appears on all pages while in demo mode

### As a Developer

**Setting Up Demo Mode:**
```bash
cd /app/backend
python3 db_seed.py seed    # Creates demo account + data
```

**Checking Demo Data:**
```bash
python3 db_seed.py stats   # View current database state
```

**Resetting Demo Data:**
```bash
python3 db_seed.py reset   # Clear all + recreate demo data
```

---

## 🔧 Technical Implementation

### Backend

**Demo User:**
- Email: `demo@aggregatoros.com`
- User ID: `demo_user_permanent`
- Flag: `is_demo: true`
- Created automatically by seed script

**Demo Data IDs:**
All demo data uses prefixed IDs:
- Programs: `demo_prog_*`
- Farmers: `demo_farmer_*`
- Claims: `demo_claim_*`
- Ledger: `demo_ledger_*`

**API Endpoint:**
```
GET /api/auth/demo-user
Returns demo user info without authentication
```

### Frontend

**Context:**
`DemoModeContext` - Manages demo mode state globally

**Components:**
- `DemoModeBanner` - Shows amber banner when active
- Login page "Try Demo" button
- Exit demo button in banner

**State Management:**
- Stored in `localStorage` as `demoMode`
- Persists across page refreshes
- Cleared when exiting demo mode

**Authentication Flow:**
```javascript
// Demo mode active
localStorage.getItem('demoMode') === 'true'
→ Fetch demo user from /api/auth/demo-user
→ Skip normal OAuth flow

// Normal mode
localStorage.getItem('demoMode') !== 'true'
→ Regular Google OAuth
→ Session-based authentication
```

---

## 📊 Demo Data Breakdown

When you seed the database, you get:

**4 Programs:**
1. Coastal Green Belt Initiative (East Godavari)
2. Krishna River Basin Afforestation (Krishna)
3. Guntur Dryland Agroforestry (Guntur)
4. Urban Fringe Carbon Sequestration (Guntur)

**65 Farmers:**
- Realistic Indian names
- Villages across Andhra Pradesh
- Phone numbers (+91 prefix)
- UPI IDs

**~220 Claims:**
- 60% approved
- 18% pending
- 22% rejected
- Geo-tagged locations
- Sample photos
- Carbon calculations

**~60 Ledger Entries:**
- Auto-generated for approved claims
- Accurate payout calculations

**Metrics:**
- ~11,000 approved trees
- ~74 tCO₂e estimated credits
- ~₹470,000 total payout

---

## 🎯 Use Cases

### 1. Product Demonstrations
**Scenario:** Showing Aggregator OS to potential clients

**Steps:**
1. Open login page
2. Click "Try Demo Mode"
3. Navigate through:
   - Dashboard → Show metrics
   - Programs → View tree programs
   - Claims → Review pending claims
   - Ledger → Check payouts
4. Exit demo when done

### 2. Feature Testing
**Scenario:** Testing new feature without real data

**Steps:**
1. Enable demo mode
2. Test feature with demo data
3. Exit and check real account unaffected

### 3. Onboarding New Users
**Scenario:** New team member learning the system

**Steps:**
1. Direct them to click "Try Demo"
2. Let them explore freely
3. When ready, they can create real account

---

## 🔐 Security & Isolation

**Data Separation:**
- ✅ Demo data isolated by user_id
- ✅ Demo IDs prefixed (`demo_*`)
- ✅ Real user data never affected
- ✅ Demo account cannot access real data

**Limitations:**
- ❌ Cannot create/edit data in demo mode (read-only)
- ❌ Cannot affect real programs/farmers/claims
- ❌ Cannot export real data
- ❌ No authentication tokens in demo mode

**Best Practices:**
- Demo mode is read-only by default
- All mutations should check if user is demo account
- Add `is_demo` flag checks in create/update endpoints

---

## 🛠️ Maintenance

### Refreshing Demo Data

**When demo data becomes stale:**
```bash
cd /app/backend
python3 db_seed.py reset  # Clears old + creates fresh data
```

**Scheduled refresh (optional):**
```bash
# Add to cron for weekly refresh
0 0 * * 0 cd /app/backend && python3 db_seed.py reset
```

### Checking Demo Account
```bash
# View demo user
mongo
use test_database
db.users.find({email: "demo@aggregatoros.com"})

# Count demo data
db.programs.count({program_id: /^demo_/})
db.farmers.count({farmer_id: /^demo_/})
```

---

## 📝 Configuration

**Customize Demo Data:**

Edit `/app/backend/seed_data.py`:

```python
# Change number of farmers per program
farmers_per_program = [20, 25, 22, 18]  # Default: [15, 20, 18, 12]

# Change claim ratios
claim_statuses = ["approved", "approved", "pending"]  # 66% approved

# Add more programs
programs_data.append({
    "name": "Your Program Name",
    # ... configuration
})
```

**Customize Demo Banner:**

Edit `/app/frontend/src/components/DemoModeBanner.js`:

```jsx
// Change colors
className="bg-gradient-to-r from-blue-50 to-indigo-50"

// Change message
<p className="text-sm">Custom demo mode message</p>
```

---

## 🐛 Troubleshooting

**Issue: "Demo user not found" error**
```bash
# Solution: Run seeder to create demo account
cd /app/backend
python3 db_seed.py seed
```

**Issue: No data showing in demo mode**
```bash
# Check if demo data exists
python3 db_seed.py stats

# Re-seed if needed
python3 db_seed.py reset
```

**Issue: Can't exit demo mode**
```bash
# Manually clear localStorage
# In browser console:
localStorage.removeItem('demoMode')
window.location.reload()
```

**Issue: Changes not saving in demo mode**
```
This is expected behavior - demo mode is read-only.
To create/edit data, exit demo mode and login.
```

---

## 📚 API Reference

### Demo Mode Endpoints

**Get Demo User**
```
GET /api/auth/demo-user

Response:
{
  "user_id": "demo_user_permanent",
  "email": "demo@aggregatoros.com",
  "name": "Demo Account",
  "is_demo": true,
  "created_at": "2024-02-21T..."
}
```

**Check if User is Demo**
```javascript
// Frontend
const { user } = useAuth();
const isDemoMode = user?.is_demo === true;

// Backend
if user.get("is_demo"):
    # Read-only mode
```

---

## 🎨 UI Components

### DemoModeBanner
```jsx
import DemoModeBanner from './components/DemoModeBanner';

// Shows amber banner when demo mode active
<DemoModeBanner />
```

### Demo Mode Context
```jsx
import { useDemoMode } from './contexts/DemoModeContext';

function MyComponent() {
  const { demoMode, toggleDemoMode } = useDemoMode();
  
  if (demoMode) {
    return <div>Viewing demo data</div>;
  }
}
```

### Try Demo Button
Already integrated in `/pages/LoginPage.js`

---

## ✅ Testing Demo Mode

**Manual Test:**
1. Navigate to login page
2. Click "Try Demo Mode"
3. Verify:
   - ✅ Banner appears at top
   - ✅ Dashboard shows data
   - ✅ All pages accessible
   - ✅ Stats match seeded data
4. Click "Exit Demo"
5. Verify:
   - ✅ Banner disappears
   - ✅ Redirected to login
   - ✅ Normal auth flow resumes

**Automated Test (Playwright):**
```javascript
test('demo mode flow', async ({ page }) => {
  await page.goto('/login');
  await page.click('[data-testid="demo-mode-btn"]');
  await expect(page.locator('text=Demo Mode Active')).toBeVisible();
  await expect(page).toHaveURL('/dashboard');
});
```

---

## 🚀 Future Enhancements

**Potential Improvements:**
- [ ] Multiple demo scenarios (beginner, advanced)
- [ ] Demo mode analytics tracking
- [ ] Guided tours in demo mode
- [ ] Demo data export disabled indicator
- [ ] "Convert to real account" button
- [ ] Demo mode time limit (auto-exit after 30 min)
- [ ] Custom demo data per industry

---

## 📖 Related Documentation

- [QUICK_START.md](../QUICK_START.md) - General setup guide
- [COMMANDS.md](../COMMANDS.md) - CLI command reference
- [backend/SEEDING_README.md](../backend/SEEDING_README.md) - Seeding details
- [memory/PRD.md](../memory/PRD.md) - Product requirements

---

**Last Updated:** Feb 21, 2026  
**Version:** 1.0  
**Status:** ✅ Production Ready
