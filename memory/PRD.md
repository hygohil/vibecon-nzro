# VanaLedger PRD

## Original Problem Statement
VanaLedger is a carbon credit management platform for agricultural projects. The app allows managing projects, farmers, activities (tree planting), credit issuances, ledger/payouts, and exports. Built with React + FastAPI + MongoDB.

## Core Requirements
- Project management (CRUD, pricing rules)
- Farmer management (CRUD, bulk onboard via CSV)
- Activity verification workflow (submit, approve/reject)
- Credit issuance lifecycle (issued -> approved -> sold -> retired)
- Auto benefit sharing on credit sale
- Payout ledger tracking
- Export (CSV, PDF dossier)
- Demo mode + Emergent Google OAuth

## What's Been Implemented

### Completed Features
- Full project CRUD with edit (name, description, payout_rate, payout_rule_type)
- Farmer CRUD with bulk CSV onboarding
- Activity submission and verification workflow
- Credit issuance with status transitions and delete with cascading benefit share removal
- Payout calculation (per_tree and per_credit modes)
- Frontend fetch caching fix (cache: 'no-store')
- Export endpoints (activity CSV, payout CSV, calculation sheet, PDF dossier)
- Dashboard stats
- Demo mode authentication
- **[2026-04-16] Survey Questions in Add Activity** — 9 farmer survey questions (main crop, crops/year, crop residue, land preparation, fertilizer, irrigation, compost, water management, program participation agreement) with single-answer radio buttons, collapsible UI, validation requiring all 9 answers, stored in backend `survey_responses` field, displayed in Review dialog with full question text + answer
- **[2026-04-16] Backfilled old activities** — All 228 existing activities backfilled with randomized survey responses via POST /api/activities/backfill-survey endpoint

### Known Issues (Pending)
- P0: Farmers page search/filter broken (only filters visible page)
- P0: Farmer Edit functionality — incomplete/unverified
- P1: Export page missing Payout CSV card
- P1: Verification page farmer dropdown was showing only 10 farmers — FIXED (page_size=9999)
- P2/P3: Minor UI/terminology fixes (login page, ledger empty state, date pickers, test IDs)
- Refactoring: FarmersPage subtitle uses hardcoded text instead of dynamic totalCount

## Tech Stack
- Frontend: React, TailwindCSS, Shadcn UI
- Backend: FastAPI, Motor (async MongoDB)
- Database: MongoDB
- Auth: Emergent Google OAuth + Demo Mode

## Key DB Schema
- projects: {project_id, payout_rule_type, payout_rate, name, ...}
- farmers: {farmer_id, project_id, approved_trees, acres, ...}
- activities: {activity_id, farmer_id, survey_responses, ...}
- ledger: Tracks payouts
- credits: {credit_id, project_id, status, ...}
- benefit_shares: Tracks automated distribution of revenue

## Prioritized Backlog
### P0
- Fix Farmers page search/filter
- Verify/complete Farmer Edit functionality

### P1
- Add Payout CSV card to Export page
- Full E2E regression testing

### P2/P3
- Login page terminology fix
- Ledger empty state terminology
- Inconsistent date pickers (use Shadcn Calendar)
- Missing test IDs on Credits page
- FarmersPage subtitle dynamic count
