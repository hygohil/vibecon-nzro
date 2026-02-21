# VanaLedger — Comprehensive Changes Plan
> Created: Feb 21, 2026
> Status: PLANNING (no code changes yet)

---

## 1. TERMINOLOGY RENAMES (Global)

The app currently uses incorrect carbon credit terminology. Here's the mapping:

| Current Term | New Term | Reason |
|---|---|---|
| `Claims` (farmer submissions) | **Activities** | Industry standard. Farmer submits a "Plantation Activity" — evidence of planting. |
| `Claims Queue` | **Verification Queue** | Aggregator verifies activities, not "claims". |
| `claim_id` | **activity_id** | Consistent with rename. |
| `claims` (MongoDB collection) | **activities** | Collection rename. |
| `ClaimCreate` / `ClaimOut` | **ActivityCreate** / **ActivityOut** | Pydantic model rename. |
| `ClaimAction` | **VerificationAction** | More accurate — it's a verification decision. |
| `claims_count` (on Program) | **activities_count** | Field rename. |
| `Total Claims` (dashboard) | **Total Activities** | UI label. |
| `Pending Review` (dashboard) | **Pending Verification** | UI label. |
| `Approved Claims` (dashboard) | **Verified Activities** | UI label. |
| `Recent Claims` (dashboard) | **Recent Activities** | UI label. |
| **NEW: Credits** | **Credits** | Actual carbon credits issued by registry AFTER verification. This is a NEW concept/section. |

### Sidebar Navigation Update
| Current | New |
|---|---|
| Dashboard | Dashboard |
| Programs | Projects (rename) |
| Farmers | Farmers |
| Claims | Verification |
| Ledger | Ledger |
| Exports | Exports |
| *(none)* | **Credits** (NEW page) |

---

## 2. FIELD REMOVALS

### Remove `village` and `district` from Farmer

**Why:** User confirmed these are not needed.

### Backend — `server.py`

| Location | Change |
|---|---|
| `FarmerCreate` model (line 78-86) | Remove `village: str` and `district: str` fields |
| `FarmerOut` model (line 88-105) | Remove `village: str` and `district: str` fields |
| `WebhookJoinPayload` model (line 145-153) | Remove `village: str` and `district: str` fields |
| `create_farmer()` endpoint (line 293-310) | No change needed (model_dump handles it) |
| `webhook_join()` endpoint (line 485-513) | Remove `"village": payload.village` and `"district": payload.district` from doc dict |
| `webhook_claim()` endpoint (line 530-536) | Remove `"farmer_village": farmer.get("village", "")` from doc |
| `ClaimOut` / `ActivityOut` model (line 118-139) | Remove `farmer_village` field |
| `action_claim()` → ledger insert (line 416-429) | Remove `"farmer_village": farmer.get("village", "")` |
| Export CSV endpoints | Remove `village` column from all CSV writers |
| Dossier PDF (line 728-734) | Remove "Geography & Villages" section (section 7) |

### Frontend

| File | Change |
|---|---|
| `FarmersPage.js` | Remove Village and District input fields from Add Farmer dialog |
| `FarmersPage.js` | Remove Village column from farmers table |
| `FarmersPage.js` | Remove village/district from search filter logic |
| `ClaimsPage.js` → (becomes `VerificationPage.js`) | Remove `farmer_village` references |
| `LedgerPage.js` | Remove Village column from ledger table |

---

## 3. NEW FEATURE: Credit Issuance & Lifecycle (Stage 6) — FULL STATUS FLOW

### What It Is
After the aggregator's verified activities are submitted to a registry (Verra, Gold Standard, ICM) and the registry approves, the aggregator manually logs the credit issuance. Credits then flow through a full lifecycle:

```
  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
  │  ISSUED  │ ──► │ APPROVED │ ──► │   SOLD   │ ──► │ RETIRED  │
  └──────────┘     └──────────┘     └──────────┘     └──────────┘
       │                                                    │
       │  Registry issues     Buyer purchases    Credits    │
       │  VCUs/CCCs           credits on market   permanently
       │                      Revenue generated   removed from
       │                                          circulation
       │
       └──── Aggregator logs issuance manually
```

### Credit Status Definitions
| Status | Meaning | Who triggers |
|---|---|---|
| `issued` | Registry has issued credits (VCUs/CCCs). Credits exist in registry. | Aggregator logs after registry confirmation |
| `approved` | Credits verified and approved for sale on market. | Aggregator marks ready for market |
| `sold` | Credits purchased by buyer. Revenue generated. | Aggregator logs sale details (buyer, price, date) |
| `retired` | Credits permanently retired (used to offset emissions). Cannot be resold. | Aggregator marks as retired after buyer retires |

### Backend Changes

#### New MongoDB Collection: `credits`
```
{
  credit_id: "credit_abc123",
  project_id: "proj_xyz",       // links to project
  user_id: "user_123",          // aggregator who logged it
  registry_name: "Verra VCS",   // Verra VCS | Gold Standard | India Carbon Market | Other
  credits_issued: 12.5,         // tCO2e actually issued by registry
  issuance_date: "2026-03-15",
  registry_reference: "VCS-1234-5678",
  serial_numbers: "VCU-001 to VCU-013",
  vintage_year: 2026,           // year the emissions reduction occurred
  notes: "First issuance for Saurashtra project",
  
  // Status lifecycle
  status: "issued",             // issued → approved → sold → retired
  
  // Approval fields (filled when status = approved)
  approved_date: null,
  
  // Sale fields (filled when status = sold)
  buyer_name: null,
  sale_price_per_credit: null,  // ₹ or $ per tCO2e
  total_revenue: null,          // credits_issued × sale_price
  sale_date: null,
  sale_currency: "INR",
  
  // Retirement fields (filled when status = retired)
  retired_date: null,
  retirement_reason: null,      // "offset" | "compliance" | "voluntary"
  retirement_beneficiary: null, // who claims the offset
  
  created_at: "2026-03-15T10:00:00Z",
  updated_at: null
}
```

#### New Pydantic Models
```python
class CreditIssuanceCreate(BaseModel):
    project_id: str
    registry_name: str                          # Verra VCS | Gold Standard | ICM | Other
    credits_issued: float                       # tCO2e
    issuance_date: str
    vintage_year: Optional[int] = 2026
    registry_reference: Optional[str] = ""
    serial_numbers: Optional[str] = ""
    notes: Optional[str] = ""

class CreditIssuanceOut(BaseModel):
    credit_id: str
    project_id: str
    project_name: Optional[str] = None
    user_id: str
    registry_name: str
    credits_issued: float
    issuance_date: str
    vintage_year: Optional[int] = None
    registry_reference: Optional[str] = ""
    serial_numbers: Optional[str] = ""
    notes: Optional[str] = ""
    status: str = "issued"
    approved_date: Optional[str] = None
    buyer_name: Optional[str] = None
    sale_price_per_credit: Optional[float] = None
    total_revenue: Optional[float] = None
    sale_date: Optional[str] = None
    sale_currency: str = "INR"
    retired_date: Optional[str] = None
    retirement_reason: Optional[str] = None
    retirement_beneficiary: Optional[str] = None
    created_at: Optional[str] = None

class CreditStatusUpdate(BaseModel):
    status: str                                  # approved | sold | retired
    # Approval
    approved_date: Optional[str] = None
    # Sale
    buyer_name: Optional[str] = None
    sale_price_per_credit: Optional[float] = None
    sale_date: Optional[str] = None
    sale_currency: Optional[str] = "INR"
    # Retirement
    retired_date: Optional[str] = None
    retirement_reason: Optional[str] = None      # offset | compliance | voluntary
    retirement_beneficiary: Optional[str] = None
    notes: Optional[str] = None
```

#### New API Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/credits` | Log a new credit issuance (status: issued) |
| `GET` | `/api/credits` | List all credits (filterable by project_id, status) |
| `GET` | `/api/credits/{credit_id}` | Get single credit detail |
| `PUT` | `/api/credits/{credit_id}/status` | Transition status: issued→approved→sold→retired |
| `PUT` | `/api/credits/{credit_id}` | Edit credit details |
| `DELETE` | `/api/credits/{credit_id}` | Delete credit record |

#### Status Transition Logic
```python
VALID_TRANSITIONS = {
    "issued": ["approved"],
    "approved": ["sold", "issued"],     # can revert to issued
    "sold": ["retired", "approved"],    # can revert to approved
    "retired": []                        # terminal state
}
```

On `sold` status: auto-calculate `total_revenue = credits_issued × sale_price_per_credit`

#### Dashboard Stats Updates
Add to dashboard response:
- `total_credits_issued` — sum of credits_issued where status in [issued, approved, sold, retired]
- `total_credits_sold` — sum where status = sold
- `total_credits_retired` — sum where status = retired
- `total_revenue` — sum of total_revenue where status = sold

### Frontend Changes

#### New Page: `CreditsPage.js`
**Route:** `/credits`

**Layout:**
- Header: "Carbon Credits" with "Log Issuance" button
- Summary cards row:
  - Total Issued (tCO2e)
  - Approved for Sale (tCO2e)
  - Sold (tCO2e) + Revenue (₹)
  - Retired (tCO2e)
- Filter tabs: All | Issued | Approved | Sold | Retired
- Credits list as cards (not table — each card has more detail):
  - Registry badge (Verra/GS/ICM)
  - Credits amount (tCO2e) — large number
  - Status badge with color
  - Issuance date, vintage year
  - Registry reference / serial numbers
  - If sold: buyer, price, revenue
  - If retired: beneficiary, reason
  - Action buttons based on current status

**Status Badge Colors:**
| Status | Color | Badge |
|---|---|---|
| `issued` | Emerald/green | `bg-emerald-50 text-emerald-700` |
| `approved` | Blue | `bg-blue-50 text-blue-700` |
| `sold` | Amber/gold | `bg-amber-50 text-amber-700` |
| `retired` | Gray | `bg-gray-100 text-gray-600` |

**Dialogs:**
1. **Log Issuance** — form: project, registry, credits, date, vintage, reference, serials, notes
2. **Approve for Sale** — confirm dialog with optional notes
3. **Record Sale** — form: buyer name, price per credit, sale date, currency
4. **Retire Credits** — form: retirement reason, beneficiary, date

**Clear labeling:** Banner at top: "These are registry-issued carbon credits (VCUs/CCCs). Distinct from estimated units."

#### Sidebar Update
Add new nav item between Verification and Ledger:
```javascript
{ to: '/credits', icon: Award, label: 'Credits' }
```
Icon: `Award` from lucide-react (represents certified/issued)

#### App.js Route Update
```javascript
import CreditsPage from './pages/CreditsPage';
// ...
<Route path="credits" element={<CreditsPage />} />
```

---

## 3b. NEW FEATURE: Auto Benefit Sharing — CONFIRMED

### What It Is
When credits are **sold** (status transitions to `sold`), the system automatically calculates each farmer's share of revenue and updates the ledger.

### Benefit Sharing Formula
```
farmer_share = (farmer_verified_trees / total_project_verified_trees) × total_revenue
```

Where:
- `farmer_verified_trees` = sum of tree_count from verified activities for this farmer in this project
- `total_project_verified_trees` = sum of all verified tree_count across all farmers in project
- `total_revenue` = credits_issued × sale_price_per_credit

### Backend Logic
When `/api/credits/{credit_id}/status` receives `status: "sold"`:

1. Calculate `total_revenue = credits_issued × sale_price_per_credit`
2. Get project_id from credit record
3. Get all verified activities for this project → sum tree_count per farmer
4. Get total verified trees for project
5. For each farmer:
   ```
   share_percentage = farmer_trees / total_trees
   farmer_revenue = share_percentage × total_revenue
   ```
6. Update ledger: increment `payable_amount` by `farmer_revenue`
7. Store breakdown in a new `benefit_shares` collection for audit trail:
   ```
   {
     share_id: "share_abc",
     credit_id: "credit_xyz",
     project_id: "proj_xyz",
     farmer_id: "farmer_abc",
     farmer_name: "Ramesh Patel",
     share_percentage: 0.285,
     trees_contributed: 100,
     total_project_trees: 350,
     revenue_share: 3571.43,
     currency: "INR",
     created_at: "2026-03-20T10:00:00Z"
   }
   ```
8. Return breakdown in response so UI can show it

### New MongoDB Collection: `benefit_shares`
Stores the audit trail of every auto-calculated share.

### New API Endpoint
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/credits/{credit_id}/shares` | Get benefit sharing breakdown for a credit issuance |

### Frontend — CreditsPage.js
When a credit is marked as "sold":
- Show a "Benefit Sharing" expandable section on the credit card
- Table showing: farmer name, trees contributed, % share, revenue share (₹)
- Total row at bottom
- Note: "Auto-calculated based on verified tree contribution"

### Ledger Page Impact
- `payable_amount` auto-increments when credits are sold
- New column or indicator: "Source" showing whether payout came from:
  - Direct project payout (per-tree rate) — existing
  - Credit sale revenue share — new

---

## 4. RENAME: "Claims" → "Activities" (Full File-by-File)

### Backend — `server.py`

#### Models (lines 107-143)
| Current | New |
|---|---|
| `class ClaimCreate` | `class ActivityCreate` |
| `class ClaimOut` | `class ActivityOut` |
| `class ClaimAction` | `class VerificationAction` |
| Field `claim_id` | `activity_id` |
| Field `farmer_village` | **REMOVE** (covered in section 2) |
| Field `verifier_notes` | Keep as-is (correct term) |

#### Webhook Models (lines 155-163)
| Current | New |
|---|---|
| `class WebhookClaimPayload` | `class WebhookActivityPayload` |

#### MongoDB Collection
| Current | New |
|---|---|
| `db.claims` | `db.activities` |

Every query that references `db.claims` must change to `db.activities`.
Approximate occurrences: ~25 across all endpoints.

#### Endpoints
| Current Route | New Route |
|---|---|
| `POST /api/claims` | `POST /api/activities` |
| `GET /api/claims` | `GET /api/activities` |
| `PUT /api/claims/{claim_id}/action` | `PUT /api/activities/{activity_id}/verify` |
| `POST /api/webhook/claim` | `POST /api/webhook/activity` |

#### Internal ID generation
| Current | New |
|---|---|
| `f"claim_{uuid...}"` | `f"activity_{uuid...}"` |

#### Dashboard Stats (line 454-481)
| Current key | New key |
|---|---|
| `total_claims` | `total_activities` |
| `pending_claims` | `pending_verification` |
| `approved_claims` | `verified_activities` |
| `recent_claims` | `recent_activities` |

#### Export Endpoints
All export endpoints that query `db.claims` → `db.activities`.
CSV column headers that say "claim_id" → "activity_id".
PDF dossier text that says "claims" → "activities".

### Frontend — File Renames

| Current File | New File |
|---|---|
| `pages/ClaimsPage.js` | `pages/VerificationPage.js` |

### Frontend — `App.js`
| Current | New |
|---|---|
| `import ClaimsPage` | `import VerificationPage` |
| `path="claims"` | `path="verification"` |

### Frontend — `Sidebar.js`
| Current | New |
|---|---|
| `{ to: '/claims', icon: ClipboardCheck, label: 'Claims' }` | `{ to: '/verification', icon: ClipboardCheck, label: 'Verification' }` |
| Add new item: | `{ to: '/credits', icon: Award, label: 'Credits' }` |

### Frontend — `DashboardPage.js`
| Current label | New label |
|---|---|
| `'Total Claims'` | `'Total Activities'` |
| `'Pending Review'` | `'Pending Verification'` |
| `'Approved Claims'` | `'Verified Activities'` |
| `'Recent Claims'` | `'Recent Activities'` |
| `stats?.total_claims` | `stats?.total_activities` |
| `stats?.pending_claims` | `stats?.pending_verification` |
| `stats?.approved_claims` | `stats?.verified_activities` |
| `stats?.recent_claims` | `stats?.recent_activities` |

### Frontend — `VerificationPage.js` (renamed from ClaimsPage.js)
Global search & replace within file:
| Current | New |
|---|---|
| `claim` | `activity` (variable names) |
| `claims` | `activities` (state variable) |
| `claim_id` | `activity_id` |
| `Claims Queue` | `Verification Queue` |
| `Add Claim` | `Submit Activity` |
| `Submit Claim` | `Submit Activity` |
| `Review Claim` | `Verify Activity` |
| `Approve` / `Reject` | Keep as-is (verification actions) |
| `Create Claim` | `Record Activity` |
| API endpoint `/claims` | `/activities` |
| API endpoint `/claims/{id}/action` | `/activities/{id}/verify` |

### Frontend — `ExportPage.js`
Update description text that references "claims" → "activities".

### Frontend — `LedgerPage.js`
Remove `farmer_village` column from table.

---

## 5. RENAME: "Programs" → "Projects" — CONFIRMED

> **Status: CONFIRMED by user.** Industry standard. Full rename required.

### Backend — `server.py`

#### Models
| Current | New |
|---|---|
| `class ProgramCreate` | `class ProjectCreate` |
| `class ProgramOut` | `class ProjectOut` |
| Field `program_id` everywhere | `project_id` |
| `program_name` on Farmer/Activity models | `project_name` |
| `payout_rule_type` | Keep |
| `claims_count` → already renamed to `activities_count` | `activities_count` |

#### MongoDB Collection
| Current | New |
|---|---|
| `db.programs` | `db.projects` |

Every query referencing `db.programs` must change to `db.projects`.
Approximate occurrences: ~20 across all endpoints.

#### API Endpoints
| Current Route | New Route |
|---|---|
| `POST /api/programs` | `POST /api/projects` |
| `GET /api/programs` | `GET /api/projects` |
| `GET /api/programs/{program_id}` | `GET /api/projects/{project_id}` |
| `DELETE /api/programs/{program_id}` | `DELETE /api/projects/{project_id}` |

#### Internal References (across ALL endpoints)
Every function parameter, variable, and query that uses `program_id` → `project_id`:
- `FarmerCreate.program_id` → `FarmerCreate.project_id`
- `FarmerOut.program_id` → `FarmerOut.project_id`
- `FarmerOut.program_name` → `FarmerOut.project_name`
- `ActivityCreate.program_id` → `ActivityCreate.project_id`
- `ActivityOut.program_id` → `ActivityOut.project_id`
- `ActivityOut.program_name` → `ActivityOut.project_name`
- `WebhookJoinPayload.program_id` → `WebhookJoinPayload.project_id`
- `WebhookActivityPayload.program_id` → `WebhookActivityPayload.project_id`
- `CreditIssuanceCreate.project_id` → already correct
- All query filters: `{"program_id": ...}` → `{"project_id": ...}`
- All doc inserts: `"program_id": ...` → `"project_id": ...`
- Dashboard stats: `user_programs` → `user_projects`
- Ledger: `"program_id"` → `"project_id"`

#### Export Endpoints
- CSV headers: `program_id` → `project_id`
- PDF dossier: "Program Name" → "Project Name", "Program Details" → "Project Details"

### Frontend

#### File Renames
| Current File | New File |
|---|---|
| `pages/ProgramsPage.js` | `pages/ProjectsPage.js` |

#### App.js
| Current | New |
|---|---|
| `import ProgramsPage from './pages/ProgramsPage'` | `import ProjectsPage from './pages/ProjectsPage'` |
| `path="programs"` | `path="projects"` |

#### Sidebar.js
| Current | New |
|---|---|
| `{ to: '/programs', icon: TreePine, label: 'Programs' }` | `{ to: '/projects', icon: TreePine, label: 'Projects' }` |

#### ProjectsPage.js (renamed from ProgramsPage.js)
Global replacements:
| Current | New |
|---|---|
| `programs` (state) | `projects` |
| `program` (variable) | `project` |
| `program_id` | `project_id` |
| `program_name` | `project_name` |
| `Create Program` | `Create Project` |
| `Programs` (heading) | `Projects` |
| `fetchPrograms` | `fetchProjects` |
| `showCreate` / dialog title | `Create Tree Project` |
| API endpoint `/programs` | `/projects` |
| `program-card-` (testid) | `project-card-` |
| `create-program-btn` | `create-project-btn` |
| `program-name-input` | `project-name-input` |
| `program-region-input` | `project-region-input` |

#### All Other Pages
Every page that references `program_id` or `programs` API:
- `FarmersPage.js` — filter by `project_id`, API call `/projects`, `farmer-program-select` → `farmer-project-select`
- `VerificationPage.js` — `project_id` references, API calls
- `LedgerPage.js` — `project_id` filter
- `ExportPage.js` — `project_id` filter, API calls
- `DashboardPage.js` — `total_programs` → `total_projects`, label "Programs" → "Projects"

---

## 6. UPDATED APP LIFECYCLE (New 7-Stage Model)

```
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: PROJECT SETUP                                      │
│  Aggregator creates Project (species, rates, controls)       │
├─────────────────────────────────────────────────────────────┤
│  Stage 2: FARMER ENROLLMENT                                  │
│  Farmers join via WhatsApp webhook or manual add             │
│  Submit: name, phone, land type, acres, UPI                  │
├─────────────────────────────────────────────────────────────┤
│  Stage 3: PLANTATION ACTIVITIES                              │
│  Farmers submit evidence via WhatsApp:                       │
│  - Tree count, species, date planted                         │
│  - Geo-tagged location (lat/lng)                             │
│  - 2 photos (sapling + wide shot)                            │
├─────────────────────────────────────────────────────────────┤
│  Stage 4: VERIFICATION                                       │
│  Aggregator reviews activities:                              │
│  - View photos + map pin                                     │
│  - Approve / Reject / Need More Info                         │
│  - On approve: estimated credits calculated                  │
├─────────────────────────────────────────────────────────────┤
│  Stage 5: MRV REPORT & REGISTRY SUBMISSION                   │
│  Export structured data for registry:                        │
│  - Project Dossier PDF                                       │
│  - Activity Data CSV                                         │
│  - Evidence Pack JSON                                        │
│  - Calculation Sheet CSV                                     │
│  - Audit Log CSV                                             │
│  Submit to Verra / Gold Standard / ICM                       │
├─────────────────────────────────────────────────────────────┤
│  Stage 6: CREDIT ISSUANCE & LIFECYCLE                        │
│  Registry approves → Aggregator logs issuance:               │
│  - Registry name, credits issued (tCO2e), serial numbers     │
│  Credit lifecycle:                                           │
│    ISSUED → APPROVED → SOLD → RETIRED                        │
│  On SOLD: auto-calculate revenue, trigger benefit sharing    │
├─────────────────────────────────────────────────────────────┤
│  Stage 7: BENEFIT SHARING & PAYOUT (AUTO)                    │
│  On credit sale, automatically:                              │
│  - Calculate each farmer's share by tree contribution %      │
│  - Update ledger with revenue share amounts                  │
│  - Store audit trail in benefit_shares collection            │
│  - Payout to farmers via UPI (future integration)            │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. SUMMARY OF FILES TO MODIFY

### Backend
| File | Changes |
|---|---|
| `server.py` | **FULL REWRITE**: Rename all models (Program→Project, Claim→Activity), rename all collections (programs→projects, claims→activities), remove village/district, add credits CRUD + status transitions + auto benefit sharing, update all endpoints, update dashboard stats, update exports |

### Frontend — File Renames
| Current File | New File |
|---|---|
| `pages/ProgramsPage.js` | **DELETE** → create `pages/ProjectsPage.js` |
| `pages/ClaimsPage.js` | **DELETE** → create `pages/VerificationPage.js` |

### Frontend — Modified Files
| File | Changes |
|---|---|
| `App.js` | Update all imports (Programs→Projects, Claims→Verification), add CreditsPage route, update route paths (/programs→/projects, /claims→/verification, add /credits) |
| `Sidebar.js` | Rename "Programs"→"Projects", "Claims"→"Verification", add "Credits" nav item with Award icon |
| `DashboardPage.js` | Update stat labels (claims→activities, programs→projects), add credits_issued + revenue metrics, update API response keys |
| `FarmersPage.js` | Remove village/district from form+table+search, rename program_id→project_id, update API endpoints /programs→/projects |
| `LedgerPage.js` | Remove village column, rename program references, add "source" indicator (project payout vs credit revenue) |
| `ExportPage.js` | Update text references: claims→activities, programs→projects |
| `LoginPage.js` | No changes needed |

### New Files
| File | Description |
|---|---|
| `pages/CreditsPage.js` | Full credit lifecycle page: log issuance, approve, sell (with auto benefit sharing), retire. Summary cards + status tabs + credit cards + dialogs |
| `pages/ProjectsPage.js` | Renamed from ProgramsPage with all program→project renames |
| `pages/VerificationPage.js` | Renamed from ClaimsPage with all claim→activity renames |

### New MongoDB Collections
| Collection | Description |
|---|---|
| `credits` | Credit issuances logged by aggregator after registry approval |
| `benefit_shares` | Auto-calculated revenue shares per farmer when credits are sold |

### MongoDB Collections Renamed
| Current | New |
|---|---|
| `programs` | `projects` |
| `claims` | `activities` |

### Data Migration
Drop all existing test data and reseed with new field names:
```bash
mongosh --eval "
use('test_database');
db.programs.drop();
db.claims.drop();
db.farmers.drop();
db.ledger.drop();
// Keep users + user_sessions (auth still works)
"
```

---

## 8. EXECUTION ORDER

1. **Backend `server.py` full rewrite** — all renames (Program→Project, Claim→Activity), remove village/district, add credits collection + CRUD + status transitions + auto benefit sharing, add benefit_shares collection, update dashboard stats, update all exports
2. **Drop test data** — remove old collections with stale field names
3. **Frontend `App.js`** — update all imports and routes
4. **Frontend `Sidebar.js`** — update nav items (Projects, Verification, Credits)
5. **Create `ProjectsPage.js`** — renamed from ProgramsPage with all renames
6. **Create `VerificationPage.js`** — renamed from ClaimsPage with all renames
7. **Create `CreditsPage.js`** — full new page with status lifecycle + benefit sharing view
8. **Update `FarmersPage.js`** — remove village/district, project_id renames
9. **Update `DashboardPage.js`** — new stat keys + credits metrics
10. **Update `LedgerPage.js`** — remove village, add revenue source indicator
11. **Update `ExportPage.js`** — text references
12. **Reseed test data** — create sample project, farmers, activities, credits
13. **Test everything** — backend API + frontend flows + export downloads

---

## 9. DECISIONS LOG

| Question | Decision | Date |
|---|---|---|
| Remove village & district? | **YES** — removed from all farmer models, forms, tables, exports | Feb 21, 2026 |
| Rename Programs → Projects? | **YES** — industry standard, full rename confirmed | Feb 21, 2026 |
| Credits page status flow? | **FULL FLOW**: issued → approved → sold → retired | Feb 21, 2026 |
| Benefit sharing mode? | **AUTO** — auto-calculate farmer shares on credit sale based on tree contribution % | Feb 21, 2026 |

---

## 10. RISK NOTES

- **Programs→Projects rename** touches every file and ~100+ references. Must be done atomically.
- **Auto benefit sharing** requires verified activities to exist before credits can be sold. UI should warn if no verified activities exist for a project.
- **Status transitions** must enforce valid paths (issued→approved→sold→retired). Cannot skip steps.
- **Existing test data** in MongoDB will break after field renames. Must drop and reseed.
