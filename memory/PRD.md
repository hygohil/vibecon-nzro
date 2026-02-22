# VanaLedger — Aggregator OS for Carbon Credit Tree Plantation

## Original Problem Statement
Build a full-stack aggregator OS for carbon credit tree plantation management. Aggregators manage multiple projects, onboard farmers, track plantation activities, manage the MRV (Monitoring, Reporting, Verification) pipeline, and handle carbon credit issuance lifecycle.

## Architecture
- **Frontend**: React + TailwindCSS + Shadcn UI (port 3000)
- **Backend**: FastAPI + Motor (async MongoDB) (port 8001, prefix `/api`)
- **Database**: MongoDB
- **Auth**: Emergent Google OAuth + Demo Mode cookie

## Core Data Collections
| Collection | Description |
|---|---|
| `projects` | Tree plantation projects (formerly programs) |
| `farmers` | Farmer registry with unique phone constraint |
| `activities` | Plantation evidence submissions (formerly claims) |
| `ledger` | Per-farmer payout tracking |
| `credits` | Registry-issued carbon credit lifecycle |
| `benefit_shares` | Auto-calculated revenue shares per credit sale |

## What's Been Implemented

### Major Refactoring (Feb 2026)
- Renamed `programs` → `projects`, `claims` → `activities` throughout frontend + backend
- Removed `village` and `district` from Farmer model
- Updated all UI terminology: Sidebar, DashboardPage, ProjectsPage, FarmersPage, VerificationPage, CreditsPage, LedgerPage, ExportPage

### Backend Rewrite
- Full FastAPI rewrite with new schema
- Pagination + sorting for farmers list
- Backend-calculated estimated credits + payouts per farmer
- Unique constraint on farmer phone number (409 Conflict on duplicate)
- Credit lifecycle: issued → approved → sold → retired
- Benefit shares auto-calculation on credit sale

### New Features
- **Credits Page**: Full lifecycle management (CreditsPage.js)
- **Bulk CSV Farmer Onboarding**: Upload CSV → validate → confirm → onboard synchronously
  - Endpoints: `/api/farmers/bulk/validate-csv`, `/api/farmers/bulk/onboard`, `/api/farmers/bulk/template`
  - Frontend: 3-step modal (Setup → Validate → Results) with error table + error report download
- **Export Center**: 6 exports — Project Dossier PDF, Activity CSV, Evidence JSON, Calculation Sheet, Payout CSV, Audit Log

### Data Quality
- Fresh seed script (`backend/seed_fresh.py`) with proper Indian names, 10-digit phones, no village/district
- 4 projects, 65 farmers, 227 activities, 4 credits in lifecycle stages, 28 benefit shares

### Bug Fixes (Feb 2026)
- Add Farmer phone validation: fixed `validatePhoneNumber` to strip `+91` before 10-digit check
- Projects page "Claims" → "Activities" label
- Dashboard "Recent Claims" → "Recent Activities"
- PDF Dossier: multi-project support + Latin-1 safe text encoding
- Payout CSV: added project_id, project_name, balance_INR columns
- Audit Log CSV: added project_id, project_name, farmer_name, farmer_phone, species
- Farmers page subtitle: uses `totalCount` not `farmers.length`
- Disclaimer: "program rules" → "project rules"
- Empty trailing CSV rows stripped before validation

## Pages & Routes
| Route | Page | Status |
|---|---|---|
| `/` or `/login` | Login (Demo mode + Google OAuth) | ✅ |
| `/dashboard` | KPI overview + Recent Activities | ✅ |
| `/projects` | Projects list + Create Project modal | ✅ |
| `/farmers` | Farmers table + Add Farmer + Bulk Upload | ✅ |
| `/verification` | Activity approval queue | ✅ |
| `/credits` | Carbon credit lifecycle | ✅ |
| `/ledger` | Payout ledger | ✅ |
| `/exports` | Export Center (6 exports) | ✅ |

## P0 Backlog (Priority)
- [ ] Auto Benefit Sharing: trigger on credit status → sold, auto-calculate + update ledger
- [ ] Farmers search + filter: make server-side (currently client-side on 10 items/page)
- [ ] Verification page farmer dropdown: fetch all 65 farmers (currently only 10)

## P1 Backlog
- [ ] Login page stale text: "programs"/"claims" → "projects"/"activities"
- [ ] Ledger page empty state: "Approve claims" → "Approve activities"
- [ ] CreditsPage: add data-testid attributes
- [ ] Date pickers: replace native with Shadcn calendar in Credits + Verification pages

## P2 / Future
- [ ] Map view for geo-evidence
- [ ] Legal & Rights Pack PDF export
- [ ] Ledger "Source" indicator (project payout vs. credit revenue)
- [ ] WhatsApp consent bulk send
- [ ] Dedup merge workflows
