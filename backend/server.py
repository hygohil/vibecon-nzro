from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, UploadFile, File, Form
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import io
import csv
import json
import httpx
from pathlib import Path
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fpdf import FPDF

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ─── Pydantic Models ───

class UserOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: Optional[str] = None

# RENAMED: ProgramCreate → ProjectCreate
class ProjectCreate(BaseModel):
    name: str
    region: str
    description: Optional[str] = ""
    species_list: List[dict] = []
    payout_rule_type: str = "per_tree"
    payout_rate: float = 50.0
    survival_rate: float = 0.7
    conservative_discount: float = 0.2
    max_trees_per_acre: int = 400
    cooldown_days: int = 30
    required_proofs: List[str] = ["location", "photo"]
    monitoring_frequency_days: int = 90

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    payout_rule_type: Optional[str] = None
    payout_rate: Optional[float] = None

# RENAMED: ProgramOut → ProjectOut, program_id → project_id, claims_count → activities_count
class ProjectOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    project_id: str
    user_id: str
    name: str
    region: str
    description: Optional[str] = ""
    species_list: List[dict] = []
    payout_rule_type: str = "per_tree"
    payout_rate: float = 50.0
    survival_rate: float = 0.7
    conservative_discount: float = 0.2
    max_trees_per_acre: int = 400
    cooldown_days: int = 30
    required_proofs: List[str] = []
    monitoring_frequency_days: int = 90
    status: str = "active"
    farmers_count: int = 0
    activities_count: int = 0
    created_at: Optional[str] = None

# REMOVED: village, district fields. RENAMED: program_id → project_id
class FarmerCreate(BaseModel):
    name: str
    phone: str
    land_type: str = "owned"
    acres: Optional[float] = None
    upi_id: Optional[str] = None
    project_id: str

class FarmerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    land_type: Optional[str] = None
    acres: Optional[float] = None
    upi_id: Optional[str] = None
    approved_trees: Optional[int] = None

# REMOVED: village, district fields. RENAMED: program_id → project_id, program_name → project_name
class FarmerOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    farmer_id: str
    name: str
    phone: str
    land_type: str = "owned"
    acres: Optional[float] = None
    upi_id: Optional[str] = None
    project_id: str
    project_name: Optional[str] = None
    status: str = "active"
    total_trees: int = 0
    approved_trees: int = 0
    estimated_credits: float = 0.0
    total_payout: float = 0.0
    estimated_credits_1y: float = 0.0  # NEW: 1-year estimate
    estimated_payout_1y: float = 0.0   # NEW: 1-year payout estimate
    created_at: Optional[str] = None

# RENAMED: ClaimCreate → ActivityCreate, program_id → project_id
class ActivityCreate(BaseModel):
    farmer_id: str
    project_id: str
    tree_count: int
    species: str
    planted_date: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    photo_urls: List[str] = []
    notes: Optional[str] = ""

# RENAMED: ClaimOut → ActivityOut, claim_id → activity_id, REMOVED: farmer_village, program_id → project_id, program_name → project_name
class ActivityOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    activity_id: str
    farmer_id: str
    farmer_name: Optional[str] = None
    farmer_phone: Optional[str] = None
    project_id: str
    project_name: Optional[str] = None
    tree_count: int
    species: str
    planted_date: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    photo_urls: List[str] = []
    notes: Optional[str] = ""
    status: str = "pending"
    estimated_credits: float = 0.0
    estimated_payout: float = 0.0
    verifier_notes: Optional[str] = ""
    created_at: Optional[str] = None
    approved_at: Optional[str] = None

# RENAMED: ClaimAction → VerificationAction
class VerificationAction(BaseModel):
    action: str
    verifier_notes: Optional[str] = ""

# REMOVED: village, district fields. RENAMED: program_id → project_id
class WebhookJoinPayload(BaseModel):
    phone: str
    name: str
    land_type: str = "owned"
    acres: Optional[float] = None
    upi_id: Optional[str] = None
    project_id: str

# RENAMED: WebhookClaimPayload → WebhookActivityPayload, program_id → project_id
class WebhookActivityPayload(BaseModel):
    phone: str
    project_id: str
    tree_count: int
    species: str
    planted_date: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    photo_urls: List[str] = []

class WebhookStatusPayload(BaseModel):
    phone: str

# NEW: Credits Models
class CreditIssuanceCreate(BaseModel):
    project_id: str
    registry_name: str  # Verra VCS | Gold Standard | India Carbon Market | Other
    credits_issued: float  # tCO2e
    issuance_date: str
    vintage_year: Optional[int] = 2026
    registry_reference: Optional[str] = ""
    serial_numbers: Optional[str] = ""
    notes: Optional[str] = ""

class CreditIssuanceOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
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
    status: str  # approved | sold | retired
    # Approval
    approved_date: Optional[str] = None
    # Sale
    buyer_name: Optional[str] = None
    sale_price_per_credit: Optional[float] = None
    sale_date: Optional[str] = None
    sale_currency: Optional[str] = "INR"
    # Retirement
    retired_date: Optional[str] = None
    retirement_reason: Optional[str] = None  # offset | compliance | voluntary
    retirement_beneficiary: Optional[str] = None
    notes: Optional[str] = None

# ─── Auth Helpers ───

EMERGENT_AUTH_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"

async def get_current_user(request: Request) -> dict:
    # Check for demo mode header or cookie
    demo_mode = request.headers.get("X-Demo-Mode") == "true" or request.cookies.get("demo_mode") == "true"
    
    if demo_mode:
        # Return demo user without authentication
        demo_user = await db.users.find_one({"email": "demo@aggregatoros.com"}, {"_id": 0})
        if demo_user:
            return demo_user
        raise HTTPException(status_code=404, detail="Demo user not found. Please run seed script.")
    
    # Normal authentication flow
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session_doc = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    expires_at = session_doc.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    user_doc = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    return user_doc

# ─── Auth Endpoints ───

@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
    body = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    async with httpx.AsyncClient() as http_client:
        resp = await http_client.get(EMERGENT_AUTH_URL, headers={"X-Session-ID": session_id})
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session")
    data = resp.json()
    email = data.get("email")
    name = data.get("name")
    picture = data.get("picture", "")
    session_token = data.get("session_token")
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        user_id = existing["user_id"]
        await db.users.update_one({"email": email}, {"$set": {"name": name, "picture": picture}})
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    response.set_cookie(key="session_token", value=session_token, httponly=True, secure=True, samesite="none", path="/", max_age=7*24*3600)
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user_doc

@api_router.get("/auth/me")
async def auth_me(request: Request):
    user = await get_current_user(request)
    return user

@api_router.get("/auth/demo-user")
async def get_demo_user():
    """Get demo user info for demo mode"""
    demo_user = await db.users.find_one({"email": "demo@aggregatoros.com"}, {"_id": 0})
    if not demo_user:
        raise HTTPException(status_code=404, detail="Demo user not found. Please run seed script first.")
    return demo_user

@api_router.post("/auth/logout")
async def auth_logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    response.delete_cookie("session_token", path="/", secure=True, samesite="none")
    return {"message": "Logged out"}

# ─── Projects (formerly Programs) ───

@api_router.post("/projects", response_model=ProjectOut)
async def create_project(project: ProjectCreate, request: Request):
    user = await get_current_user(request)
    doc = project.model_dump()
    doc["project_id"] = f"proj_{uuid.uuid4().hex[:10]}"
    doc["user_id"] = user["user_id"]
    doc["status"] = "active"
    doc["farmers_count"] = 0
    doc["activities_count"] = 0
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.projects.insert_one(doc)
    result = await db.projects.find_one({"project_id": doc["project_id"]}, {"_id": 0})
    return ProjectOut(**result)

@api_router.get("/projects", response_model=List[ProjectOut])
async def list_projects(request: Request):
    user = await get_current_user(request)
    projects = await db.projects.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(1000)
    for p in projects:
        p["farmers_count"] = await db.farmers.count_documents({"project_id": p["project_id"]})
        p["activities_count"] = await db.activities.count_documents({"project_id": p["project_id"]})
    return [ProjectOut(**p) for p in projects]

@api_router.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, request: Request):
    user = await get_current_user(request)
    p = await db.projects.find_one({"project_id": project_id, "user_id": user["user_id"]}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    p["farmers_count"] = await db.farmers.count_documents({"project_id": project_id})
    p["activities_count"] = await db.activities.count_documents({"project_id": project_id})
    return ProjectOut(**p)

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, request: Request):
    user = await get_current_user(request)
    result = await db.projects.delete_one({"project_id": project_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted"}

@api_router.put("/projects/{project_id}", response_model=ProjectOut)
async def update_project(project_id: str, update: ProjectUpdate, request: Request):
    user = await get_current_user(request)
    project = await db.projects.find_one({"project_id": project_id, "user_id": user["user_id"]}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    changes = {k: v for k, v in update.model_dump().items() if v is not None}
    if "payout_rate" in changes and changes["payout_rate"] <= 0:
        raise HTTPException(status_code=400, detail="payout_rate must be positive")
    if changes:
        await db.projects.update_one({"project_id": project_id}, {"$set": changes})
    p = await db.projects.find_one({"project_id": project_id, "user_id": user["user_id"]}, {"_id": 0})
    p["farmers_count"] = await db.farmers.count_documents({"project_id": project_id})
    p["activities_count"] = await db.activities.count_documents({"project_id": project_id})
    return ProjectOut(**p)

# ─── Farmers ───

# ─── Farmers ───

# Annual CO2 estimate constant (kg per tree per year)
ESTIMATED_CO2_KG_PER_TREE_PER_YEAR = 20.0

def calculate_farmer_estimates(farmer: dict, project: dict) -> dict:
    """
    Calculate 1-year estimated credits and payout for a farmer
    based on their approved trees, land area, and project parameters.
    Respects payout_rule_type: 'per_tree' or 'per_credit'.
    """
    acres = farmer.get("acres", 0) or 0
    approved_trees = farmer.get("approved_trees", 0)

    # Get project parameters
    max_trees_per_acre = project.get("max_trees_per_acre", 400)
    survival_rate = project.get("survival_rate", 0.7)
    conservative_discount = project.get("conservative_discount", 0.2)
    payout_rate = project.get("payout_rate", 500.0)
    payout_rule_type = project.get("payout_rule_type", "per_credit")

    # Calculate max allowed trees based on land area
    max_allowed_trees = acres * max_trees_per_acre if acres > 0 else approved_trees

    # Effective trees for estimate (capped by land capacity)
    effective_trees = min(approved_trees, max_allowed_trees)

    # tCO2e credits: always calculated for display purposes
    tco2_per_tree_per_year = ESTIMATED_CO2_KG_PER_TREE_PER_YEAR / 1000.0
    estimated_credits_1y = effective_trees * tco2_per_tree_per_year * survival_rate * (1 - conservative_discount)

    # Payout depends on rule type
    if payout_rule_type == "per_tree":
        estimated_payout_1y = effective_trees * payout_rate
    else:
        estimated_payout_1y = estimated_credits_1y * payout_rate

    return {
        "estimated_credits_1y": round(estimated_credits_1y, 4),
        "estimated_payout_1y": round(estimated_payout_1y, 0)
    }

@api_router.post("/farmers", response_model=FarmerOut)
async def create_farmer(farmer: FarmerCreate, request: Request):
    user = await get_current_user(request)
    
    # Validate land_type
    if farmer.land_type not in ["owned", "leased"]:
        raise HTTPException(status_code=400, detail="land_type must be 'owned' or 'leased'")
    
    # Check if phone number already exists (uniqueness check)
    existing = await db.farmers.find_one({"phone": farmer.phone}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=409, detail="This mobile number is already registered")
    
    project = await db.projects.find_one({"project_id": farmer.project_id, "user_id": user["user_id"]}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    doc = farmer.model_dump()
    doc["farmer_id"] = f"farmer_{uuid.uuid4().hex[:10]}"
    doc["project_name"] = project["name"]
    doc["status"] = "active"
    doc["total_trees"] = 0
    doc["approved_trees"] = 0
    doc["estimated_credits"] = 0.0
    doc["total_payout"] = 0.0
    doc["land_type"] = farmer.land_type.lower()  # Normalize to lowercase
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.farmers.insert_one(doc)
    result = await db.farmers.find_one({"farmer_id": doc["farmer_id"]}, {"_id": 0})
    
    # Calculate 1-year estimates
    estimates = calculate_farmer_estimates(result, project)
    result.update(estimates)
    
    return FarmerOut(**result)

@api_router.get("/farmers", response_model=List[FarmerOut])
async def list_farmers(request: Request, project_id: Optional[str] = None, page: int = 1, page_size: int = 10):
    user = await get_current_user(request)
    user_projects = await db.projects.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(1000)
    project_ids = [p["project_id"] for p in user_projects]
    projects_map = {p["project_id"]: p for p in user_projects}
    
    query = {"project_id": {"$in": project_ids}}
    if project_id:
        query["project_id"] = project_id
    
    # Count total for pagination
    total_count = await db.farmers.count_documents(query)
    
    # Pagination with newest first (created_at DESC)
    skip = (page - 1) * page_size
    farmers = await db.farmers.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(page_size).to_list(page_size)
    
    # Calculate 1-year estimates for each farmer
    for f in farmers:
        project = projects_map.get(f["project_id"])
        if project:
            estimates = calculate_farmer_estimates(f, project)
            f.update(estimates)
        else:
            f["estimated_credits_1y"] = 0.0
            f["estimated_payout_1y"] = 0.0
    
    # Add pagination metadata to response header (optional)
    # Could also return as wrapped response with {data, total, page, page_size}
    return [FarmerOut(**f) for f in farmers]

@api_router.delete("/farmers/{farmer_id}")
async def delete_farmer(farmer_id: str, request: Request):
    user = await get_current_user(request)
    farmer = await db.farmers.find_one({"farmer_id": farmer_id}, {"_id": 0, "project_id": 1, "name": 1})
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    # Verify farmer belongs to a project owned by this user
    project = await db.projects.find_one({"project_id": farmer["project_id"], "user_id": user["user_id"]}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=403, detail="Not authorised")
    # Cascade delete
    await db.farmers.delete_one({"farmer_id": farmer_id})
    await db.activities.delete_many({"farmer_id": farmer_id})
    await db.ledger.delete_many({"farmer_id": farmer_id})
    await db.benefit_shares.delete_many({"farmer_id": farmer_id})
    return {"deleted": True, "farmer_id": farmer_id, "name": farmer["name"]}


@api_router.get("/farmers/{farmer_id}", response_model=FarmerOut)
async def get_farmer(farmer_id: str, request: Request):
    _ = await get_current_user(request)  # Authentication check
    farmer = await db.farmers.find_one({"farmer_id": farmer_id}, {"_id": 0})
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    
    # Calculate 1-year estimates
    project = await db.projects.find_one({"project_id": farmer.get("project_id")}, {"_id": 0})
    if project:
        estimates = calculate_farmer_estimates(farmer, project)
        farmer.update(estimates)
    else:
        farmer["estimated_credits_1y"] = 0.0
        farmer["estimated_payout_1y"] = 0.0
    
    return FarmerOut(**farmer)

@api_router.get("/farmers/count/total")
async def get_farmers_count(request: Request, project_id: Optional[str] = None):
    """Get total count of farmers for pagination"""
    user = await get_current_user(request)
    user_projects = await db.projects.find({"user_id": user["user_id"]}, {"_id": 0, "project_id": 1}).to_list(1000)
    project_ids = [p["project_id"] for p in user_projects]
    query = {"project_id": {"$in": project_ids}}
    if project_id:
        query["project_id"] = project_id
    total = await db.farmers.count_documents(query)
    return {"total": total}

@api_router.post("/farmers/check-phone")
async def check_phone_uniqueness(body: dict, request: Request):
    """Check if phone number is already registered"""
    _ = await get_current_user(request)  # Authentication check
    phone = body.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="phone is required")
    
    existing = await db.farmers.find_one({"phone": phone}, {"_id": 0, "farmer_id": 1, "name": 1})
    if existing:
        return {"exists": True, "message": "This mobile number is already registered"}
    return {"exists": False}


# ─── Bulk Farmer Onboarding ───────────────────────────────────────────────────

def _normalize_phone(raw: str) -> str:
    """Return the 10-digit national number, stripping +91 if present."""
    s = raw.strip().replace(" ", "")
    if s.startswith("+91"):
        s = s[3:]
    return s.replace("-", "").replace("(", "").replace(")", "")

def _validate_bulk_row(row: dict, row_num: int) -> list[str]:
    errors = []
    name = (row.get("name") or "").strip()
    phone = _normalize_phone(row.get("phone") or "")
    land_type = (row.get("land_type") or "").strip().lower()
    acres_raw = (row.get("acres") or "").strip()

    if not name:
        errors.append("name is required")
    elif len(name) > 100:
        errors.append("name must be ≤ 100 characters")

    if not phone:
        errors.append("phone is required")
    elif not phone.isdigit():
        errors.append("phone must contain digits only")
    elif len(phone) != 10:
        errors.append(f"phone must be 10 digits (got {len(phone)})")
    elif phone[0] not in "6789":
        errors.append("phone must start with 6, 7, 8, or 9")

    if land_type not in ("owned", "leased"):
        errors.append("land_type must be 'owned' or 'leased'")

    if acres_raw:
        try:
            acres = float(acres_raw)
            if acres <= 0:
                errors.append("acres must be a positive number")
        except ValueError:
            errors.append(f"acres must be a number (got '{acres_raw}')")

    return errors


@api_router.post("/farmers/bulk/validate-csv")
async def bulk_validate_csv(
    request: Request,
    file: UploadFile = File(...),
    project_id: str = Form(...)
):
    """
    Step 1: Parse CSV + validate all rows. No DB writes.
    Returns per-row validation results + phone duplicate check.
    """
    user = await get_current_user(request)

    # Validate project belongs to user
    project = await db.projects.find_one({"project_id": project_id, "user_id": user["user_id"]}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Read CSV
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")  # handle BOM
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    required_headers = {"name", "phone", "land_type"}
    actual_headers = set(h.strip().lower() for h in (reader.fieldnames or []))
    missing = required_headers - actual_headers
    if missing:
        raise HTTPException(status_code=400, detail=f"CSV missing required columns: {', '.join(sorted(missing))}")

    rows = []
    phone_seen = {}  # track intra-CSV duplicates

    for i, raw_row in enumerate(reader, start=2):
        # Skip completely empty rows (trailing newlines)
        if not any((v or "").strip() for v in raw_row.values()):
            continue
        normalized = {k.strip().lower(): (v or "").strip() for k, v in raw_row.items()}
        phone_10 = _normalize_phone(normalized.get("phone", ""))
        errors = _validate_bulk_row(normalized, i)

        # Intra-CSV duplicate check
        if phone_10 and phone_10.isdigit() and len(phone_10) == 10:
            if phone_10 in phone_seen:
                errors.append(f"Duplicate phone in CSV (already on row {phone_seen[phone_10]})")
            else:
                phone_seen[phone_10] = i

        rows.append({
            "row": i,
            "name": normalized.get("name", ""),
            "phone": phone_10,
            "phone_raw": normalized.get("phone", ""),
            "land_type": normalized.get("land_type", "").lower(),
            "acres": normalized.get("acres", ""),
            "upi_id": normalized.get("upi_id", ""),
            "errors": errors,
        })

    if not rows:
        raise HTTPException(status_code=400, detail="CSV file is empty (no data rows)")

    # Batch DB duplicate check for valid phones
    valid_phones = [r["phone"] for r in rows if not r["errors"] and r["phone"]]
    if valid_phones:
        existing_docs = await db.farmers.find({"phone": {"$in": valid_phones}}, {"_id": 0, "phone": 1, "name": 1}).to_list(10000)
        existing_map = {d["phone"]: d["name"] for d in existing_docs}
        for r in rows:
            if r["phone"] in existing_map:
                r["errors"].append(f"Phone already registered to '{existing_map[r['phone']]}'")

    # Final valid/error split
    valid_rows = [r for r in rows if not r["errors"]]
    error_rows = [r for r in rows if r["errors"]]

    return {
        "project_id": project_id,
        "project_name": project["name"],
        "total_rows": len(rows),
        "valid_count": len(valid_rows),
        "error_count": len(error_rows),
        "rows": rows,
    }


@api_router.post("/farmers/bulk/onboard")
async def bulk_onboard_farmers(body: dict, request: Request):
    """
    Step 2: Synchronously onboard all validated rows.
    Accepts {project_id, rows: [{name, phone, land_type, acres, upi_id}]}
    """
    user = await get_current_user(request)
    project_id = body.get("project_id")
    rows = body.get("rows", [])

    if not project_id or not rows:
        raise HTTPException(status_code=400, detail="project_id and rows are required")

    project = await db.projects.find_one({"project_id": project_id, "user_id": user["user_id"]}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    successes = []
    errors = []

    for r in rows:
        row_num = r.get("row", "?")
        phone = _normalize_phone(str(r.get("phone", "")))
        name = (r.get("name") or "").strip()
        land_type = (r.get("land_type") or "owned").strip().lower()
        acres_raw = r.get("acres", "")
        upi_id = (r.get("upi_id") or "").strip()

        try:
            acres = float(acres_raw) if acres_raw else None
        except (ValueError, TypeError):
            acres = None

        # Re-validate (defense against bypasses)
        re_errors = _validate_bulk_row({
            "name": name, "phone": phone, "land_type": land_type,
            "acres": str(acres) if acres else "", "upi_id": upi_id
        }, row_num)
        if re_errors:
            errors.append({"row": row_num, "name": name, "phone": phone, "reason": "; ".join(re_errors)})
            continue

        # Final uniqueness check
        existing = await db.farmers.find_one({"phone": phone}, {"_id": 0, "name": 1})
        if existing:
            errors.append({"row": row_num, "name": name, "phone": phone, "reason": f"Phone already registered to '{existing['name']}'"})
            continue

        doc = {
            "farmer_id": f"farmer_{uuid.uuid4().hex[:10]}",
            "name": name,
            "phone": phone,
            "land_type": land_type,
            "acres": acres,
            "upi_id": upi_id,
            "project_id": project_id,
            "project_name": project["name"],
            "status": "active",
            "total_trees": 0,
            "approved_trees": 0,
            "estimated_credits": 0.0,
            "total_payout": 0.0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.farmers.insert_one(doc)
        successes.append({"row": row_num, "name": name, "phone": phone, "farmer_id": doc["farmer_id"]})

    return {
        "project_id": project_id,
        "project_name": project["name"],
        "success_count": len(successes),
        "error_count": len(errors),
        "successes": successes,
        "errors": errors,
    }


@api_router.get("/farmers/bulk/template")
async def download_bulk_template(request: Request):
    """Return a demo CSV template with sample Indian farmer data."""
    _ = await get_current_user(request)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "phone", "land_type", "acres", "upi_id"])
    sample_rows = [
        ["Venkatesh Reddy",      "9876543210", "owned",  "3.5",  "venkatesh10@gpay"],
        ["Saraswathi Devi",      "8765432109", "owned",  "2.0",  "saraswathi22@paytm"],
        ["Ramakrishna Naidu",    "7654321098", "leased", "5.0",  "rama45@phonepe"],
        ["Anjaneyulu Prasad",    "9123456780", "owned",  "1.5",  "anju99@ybl"],
        ["Padmavathi Reddy",     "8234567891", "leased", "4.0",  "padma11@oksbi"],
        ["Nageswara Rao",        "7345678902", "owned",  "6.5",  "nageswara33@gpay"],
        ["Bhavani Devi",         "9456789013", "owned",  "2.5",  "bhavani07@paytm"],
        ["Krishnamurthy Iyer",   "8567890124", "leased", "3.0",  "krishna88@phonepe"],
        ["Lakshmi Bai",          "9678901235", "owned",  "1.0",  ""],
        ["Obulaiah Reddy",       "7789012346", "owned",  "7.5",  "obulaiah55@gpay"],
    ]
    for row in sample_rows:
        writer.writerow(row)
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=farmer_bulk_template.csv"}
    )

# ─── Activities (formerly Claims) ───

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

def calculate_credits(tree_count: int, species: str, survival_rate: float, discount: float) -> float:
    bucket = get_species_bucket(species)
    rate = SPECIES_RATES.get(bucket, 0.01)
    return round(tree_count * rate * survival_rate * (1 - discount), 4)

@api_router.post("/activities", response_model=ActivityOut)
async def create_activity(activity: ActivityCreate, request: Request):
    _ = await get_current_user(request)  # Authentication check
    project = await db.projects.find_one({"project_id": activity.project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    farmer = await db.farmers.find_one({"farmer_id": activity.farmer_id}, {"_id": 0})
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    survival = project.get("survival_rate", 0.7)
    discount = project.get("conservative_discount", 0.2)
    est_credits = calculate_credits(activity.tree_count, activity.species, survival, discount)
    if project.get("payout_rule_type") == "per_tree":
        est_payout = round(activity.tree_count * project.get("payout_rate", 50), 2)
    else:
        est_payout = round(est_credits * project.get("payout_rate", 500), 2)
    doc = activity.model_dump()
    doc["activity_id"] = f"activity_{uuid.uuid4().hex[:10]}"
    doc["farmer_name"] = farmer.get("name")
    doc["farmer_phone"] = farmer.get("phone")
    doc["project_name"] = project.get("name")
    doc["status"] = "pending"
    doc["estimated_credits"] = est_credits
    doc["estimated_payout"] = est_payout
    doc["verifier_notes"] = ""
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    doc["approved_at"] = None
    await db.activities.insert_one(doc)
    await db.farmers.update_one({"farmer_id": activity.farmer_id}, {"$inc": {"total_trees": activity.tree_count}})
    result = await db.activities.find_one({"activity_id": doc["activity_id"]}, {"_id": 0})
    return ActivityOut(**result)

@api_router.get("/activities", response_model=List[ActivityOut])
async def list_activities(request: Request, project_id: Optional[str] = None, status: Optional[str] = None):
    user = await get_current_user(request)
    user_projects = await db.projects.find({"user_id": user["user_id"]}, {"_id": 0, "project_id": 1}).to_list(1000)
    project_ids = [p["project_id"] for p in user_projects]
    query = {"project_id": {"$in": project_ids}}
    if project_id:
        query["project_id"] = project_id
    if status:
        query["status"] = status
    activities = await db.activities.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [ActivityOut(**a) for a in activities]

@api_router.put("/activities/{activity_id}/verify")
async def verify_activity(activity_id: str, action: VerificationAction, request: Request):
    _ = await get_current_user(request)  # Authentication check
    activity = await db.activities.find_one({"activity_id": activity_id}, {"_id": 0})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if action.action == "approve":
        new_status = "approved"
        approved_at = datetime.now(timezone.utc).isoformat()
        await db.activities.update_one({"activity_id": activity_id}, {"$set": {"status": new_status, "verifier_notes": action.verifier_notes, "approved_at": approved_at}})
        await db.farmers.update_one({"farmer_id": activity["farmer_id"]}, {"$inc": {"approved_trees": activity["tree_count"], "estimated_credits": activity["estimated_credits"], "total_payout": activity["estimated_payout"]}})
        existing = await db.ledger.find_one({"farmer_id": activity["farmer_id"]}, {"_id": 0})
        if existing:
            await db.ledger.update_one({"farmer_id": activity["farmer_id"]}, {"$inc": {"approved_trees_total": activity["tree_count"], "approved_credits_total": activity["estimated_credits"], "payable_amount": activity["estimated_payout"]}})
        else:
            farmer = await db.farmers.find_one({"farmer_id": activity["farmer_id"]}, {"_id": 0})
            await db.ledger.insert_one({
                "ledger_id": f"ledger_{uuid.uuid4().hex[:10]}",
                "farmer_id": activity["farmer_id"],
                "farmer_name": farmer.get("name", ""),
                "farmer_phone": farmer.get("phone", ""),
                "upi_id": farmer.get("upi_id", ""),
                "project_id": activity["project_id"],
                "project_name": activity.get("project_name", ""),
                "approved_trees_total": activity["tree_count"],
                "approved_credits_total": activity["estimated_credits"],
                "payable_amount": activity["estimated_payout"],
                "paid_amount": 0.0,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
    elif action.action == "reject":
        await db.activities.update_one({"activity_id": activity_id}, {"$set": {"status": "rejected", "verifier_notes": action.verifier_notes}})
    elif action.action == "needs_info":
        await db.activities.update_one({"activity_id": activity_id}, {"$set": {"status": "needs_info", "verifier_notes": action.verifier_notes}})
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    updated = await db.activities.find_one({"activity_id": activity_id}, {"_id": 0})
    return updated

# ─── Ledger ───

@api_router.get("/ledger")
async def get_ledger(request: Request, project_id: Optional[str] = None):
    user = await get_current_user(request)
    user_projects = await db.projects.find({"user_id": user["user_id"]}, {"_id": 0, "project_id": 1}).to_list(1000)
    project_ids = [p["project_id"] for p in user_projects]
    query = {"project_id": {"$in": project_ids}}
    if project_id:
        query["project_id"] = project_id
    ledger_entries = await db.ledger.find(query, {"_id": 0}).to_list(1000)
    return ledger_entries

# ─── Dashboard Stats ───

@api_router.get("/dashboard/stats")
async def dashboard_stats(request: Request):
    user = await get_current_user(request)
    user_projects = await db.projects.find({"user_id": user["user_id"]}, {"_id": 0, "project_id": 1, "name": 1}).to_list(1000)
    project_ids = [p["project_id"] for p in user_projects]
    total_projects = len(project_ids)
    total_farmers = await db.farmers.count_documents({"project_id": {"$in": project_ids}})
    total_activities = await db.activities.count_documents({"project_id": {"$in": project_ids}})
    pending_verification = await db.activities.count_documents({"project_id": {"$in": project_ids}, "status": "pending"})
    verified_activities = await db.activities.count_documents({"project_id": {"$in": project_ids}, "status": "approved"})
    pipeline = [
        {"$match": {"project_id": {"$in": project_ids}, "status": "approved"}},
        {"$group": {"_id": None, "total_trees": {"$sum": "$tree_count"}, "total_credits": {"$sum": "$estimated_credits"}, "total_payout": {"$sum": "$estimated_payout"}}}
    ]
    agg = await db.activities.aggregate(pipeline).to_list(1)
    totals = agg[0] if agg else {"total_trees": 0, "total_credits": 0, "total_payout": 0}
    
    # Credits stats
    credits_pipeline_issued = [
        {"$match": {"project_id": {"$in": project_ids}}},
        {"$group": {"_id": None, "total": {"$sum": "$credits_issued"}}}
    ]
    credits_agg_issued = await db.credits.aggregate(credits_pipeline_issued).to_list(1)
    total_credits_issued = credits_agg_issued[0]["total"] if credits_agg_issued else 0
    
    credits_pipeline_sold = [
        {"$match": {"project_id": {"$in": project_ids}, "status": "sold"}},
        {"$group": {"_id": None, "total_sold": {"$sum": "$credits_issued"}, "total_revenue": {"$sum": "$total_revenue"}}}
    ]
    credits_agg_sold = await db.credits.aggregate(credits_pipeline_sold).to_list(1)
    total_credits_sold = credits_agg_sold[0]["total_sold"] if credits_agg_sold else 0
    total_revenue = credits_agg_sold[0]["total_revenue"] if credits_agg_sold else 0
    
    recent_activities = await db.activities.find({"project_id": {"$in": project_ids}}, {"_id": 0}).sort("created_at", -1).to_list(5)
    return {
        "total_projects": total_projects,
        "total_farmers": total_farmers,
        "total_activities": total_activities,
        "pending_verification": pending_verification,
        "verified_activities": verified_activities,
        "approved_trees": totals.get("total_trees", 0),
        "estimated_credits": round(totals.get("total_credits", 0), 4),
        "total_payout": round(totals.get("total_payout", 0), 2),
        "total_credits_issued": round(total_credits_issued, 4),
        "total_credits_sold": round(total_credits_sold, 4),
        "total_revenue": round(total_revenue, 2),
        "recent_activities": recent_activities
    }

# ─── Credits Endpoints (NEW) ───

VALID_CREDIT_TRANSITIONS = {
    "issued": ["approved"],
    "approved": ["sold", "issued"],
    "sold": ["retired", "approved"],
    "retired": []
}

@api_router.post("/credits", response_model=CreditIssuanceOut)
async def log_credit_issuance(credit: CreditIssuanceCreate, request: Request):
    user = await get_current_user(request)
    project = await db.projects.find_one({"project_id": credit.project_id, "user_id": user["user_id"]}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    doc = credit.model_dump()
    doc["credit_id"] = f"credit_{uuid.uuid4().hex[:10]}"
    doc["user_id"] = user["user_id"]
    doc["project_name"] = project["name"]
    doc["status"] = "issued"
    doc["approved_date"] = None
    doc["buyer_name"] = None
    doc["sale_price_per_credit"] = None
    doc["total_revenue"] = None
    doc["sale_date"] = None
    doc["sale_currency"] = "INR"
    doc["retired_date"] = None
    doc["retirement_reason"] = None
    doc["retirement_beneficiary"] = None
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    doc["updated_at"] = None
    await db.credits.insert_one(doc)
    result = await db.credits.find_one({"credit_id": doc["credit_id"]}, {"_id": 0})
    return CreditIssuanceOut(**result)

@api_router.get("/credits", response_model=List[CreditIssuanceOut])
async def list_credits(request: Request, project_id: Optional[str] = None, status: Optional[str] = None):
    user = await get_current_user(request)
    user_projects = await db.projects.find({"user_id": user["user_id"]}, {"_id": 0, "project_id": 1}).to_list(1000)
    project_ids = [p["project_id"] for p in user_projects]
    query = {"project_id": {"$in": project_ids}}
    if project_id:
        query["project_id"] = project_id
    if status:
        query["status"] = status
    credits = await db.credits.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [CreditIssuanceOut(**c) for c in credits]

@api_router.get("/credits/{credit_id}", response_model=CreditIssuanceOut)
async def get_credit(credit_id: str, request: Request):
    user = await get_current_user(request)
    credit = await db.credits.find_one({"credit_id": credit_id, "user_id": user["user_id"]}, {"_id": 0})
    if not credit:
        raise HTTPException(status_code=404, detail="Credit not found")
    return CreditIssuanceOut(**credit)

@api_router.put("/credits/{credit_id}/status")
async def update_credit_status(credit_id: str, update: CreditStatusUpdate, request: Request):
    user = await get_current_user(request)
    credit = await db.credits.find_one({"credit_id": credit_id, "user_id": user["user_id"]}, {"_id": 0})
    if not credit:
        raise HTTPException(status_code=404, detail="Credit not found")
    
    # Validate transition
    current_status = credit["status"]
    new_status = update.status
    if new_status not in VALID_CREDIT_TRANSITIONS.get(current_status, []):
        raise HTTPException(status_code=400, detail=f"Invalid status transition: {current_status} -> {new_status}")
    
    update_doc = {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}
    
    if new_status == "approved":
        update_doc["approved_date"] = update.approved_date or datetime.now(timezone.utc).isoformat()
    
    elif new_status == "sold":
        # Calculate total revenue
        if not update.sale_price_per_credit:
            raise HTTPException(status_code=400, detail="sale_price_per_credit required for sold status")
        total_revenue = credit["credits_issued"] * update.sale_price_per_credit
        update_doc.update({
            "buyer_name": update.buyer_name,
            "sale_price_per_credit": update.sale_price_per_credit,
            "total_revenue": round(total_revenue, 2),
            "sale_date": update.sale_date or datetime.now(timezone.utc).isoformat(),
            "sale_currency": update.sale_currency or "INR"
        })
        
        # AUTO BENEFIT SHARING - Calculate farmer shares
        project_id = credit["project_id"]
        
        # Get all verified activities for this project
        verified_activities = await db.activities.find({"project_id": project_id, "status": "approved"}, {"_id": 0}).to_list(10000)
        
        # Calculate total verified trees
        total_project_trees = sum(a["tree_count"] for a in verified_activities)
        
        if total_project_trees > 0:
            # Calculate shares per farmer
            farmer_trees = {}
            for activity in verified_activities:
                farmer_id = activity["farmer_id"]
                farmer_trees[farmer_id] = farmer_trees.get(farmer_id, 0) + activity["tree_count"]
            
            # Create benefit shares and update ledger
            for farmer_id, trees in farmer_trees.items():
                share_percentage = trees / total_project_trees
                revenue_share = round(total_revenue * share_percentage, 2)
                
                # Get farmer info
                farmer = await db.farmers.find_one({"farmer_id": farmer_id}, {"_id": 0})
                
                # Store benefit share record
                await db.benefit_shares.insert_one({
                    "share_id": f"share_{uuid.uuid4().hex[:10]}",
                    "credit_id": credit_id,
                    "project_id": project_id,
                    "farmer_id": farmer_id,
                    "farmer_name": farmer.get("name", ""),
                    "share_percentage": round(share_percentage, 4),
                    "trees_contributed": trees,
                    "total_project_trees": total_project_trees,
                    "revenue_share": revenue_share,
                    "currency": update.sale_currency or "INR",
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                
                # Update ledger - increment payable_amount
                await db.ledger.update_one(
                    {"farmer_id": farmer_id},
                    {"$inc": {"payable_amount": revenue_share}}
                )
    
    elif new_status == "retired":
        update_doc.update({
            "retired_date": update.retired_date or datetime.now(timezone.utc).isoformat(),
            "retirement_reason": update.retirement_reason,
            "retirement_beneficiary": update.retirement_beneficiary
        })
    
    if update.notes:
        update_doc["notes"] = update.notes
    
    await db.credits.update_one({"credit_id": credit_id}, {"$set": update_doc})
    updated = await db.credits.find_one({"credit_id": credit_id}, {"_id": 0})
    return updated

@api_router.get("/credits/{credit_id}/shares")
async def get_credit_shares(credit_id: str, request: Request):
    user = await get_current_user(request)
    credit = await db.credits.find_one({"credit_id": credit_id, "user_id": user["user_id"]}, {"_id": 0})
    if not credit:
        raise HTTPException(status_code=404, detail="Credit not found")
    shares = await db.benefit_shares.find({"credit_id": credit_id}, {"_id": 0}).to_list(1000)
    return shares

@api_router.put("/credits/{credit_id}")
async def update_credit(credit_id: str, updates: dict, request: Request):
    user = await get_current_user(request)
    credit = await db.credits.find_one({"credit_id": credit_id, "user_id": user["user_id"]}, {"_id": 0})
    if not credit:
        raise HTTPException(status_code=404, detail="Credit not found")
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.credits.update_one({"credit_id": credit_id}, {"$set": updates})
    updated = await db.credits.find_one({"credit_id": credit_id}, {"_id": 0})
    return updated

@api_router.delete("/credits/{credit_id}")
async def delete_credit(credit_id: str, request: Request):
    user = await get_current_user(request)
    credit = await db.credits.find_one({"credit_id": credit_id, "user_id": user["user_id"]}, {"_id": 0, "status": 1, "credits_issued": 1})
    if not credit:
        raise HTTPException(status_code=404, detail="Credit not found")
    await db.credits.delete_one({"credit_id": credit_id})
    await db.benefit_shares.delete_many({"credit_id": credit_id})
    return {"deleted": True, "credit_id": credit_id, "status": credit.get("status"), "credits_issued": credit.get("credits_issued")}

# ─── WhatsApp Webhook Endpoints ───

@api_router.post("/webhook/join")
async def webhook_join(payload: WebhookJoinPayload):
    project = await db.projects.find_one({"project_id": payload.project_id}, {"_id": 0})
    if not project:
        return {"success": False, "message": "Project not found"}
    existing = await db.farmers.find_one({"phone": payload.phone, "project_id": payload.project_id}, {"_id": 0})
    if existing:
        return {"success": True, "message": f"Already enrolled in {project['name']}", "farmer_id": existing["farmer_id"]}
    farmer_id = f"farmer_{uuid.uuid4().hex[:10]}"
    doc = {
        "farmer_id": farmer_id,
        "name": payload.name,
        "phone": payload.phone,
        "land_type": payload.land_type,
        "acres": payload.acres,
        "upi_id": payload.upi_id,
        "project_id": payload.project_id,
        "project_name": project["name"],
        "status": "active",
        "total_trees": 0,
        "approved_trees": 0,
        "estimated_credits": 0.0,
        "total_payout": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.farmers.insert_one(doc)
    return {"success": True, "message": f"Enrolled in {project['name']}", "farmer_id": farmer_id}

@api_router.post("/webhook/activity")
async def webhook_activity(payload: WebhookActivityPayload):
    farmer = await db.farmers.find_one({"phone": payload.phone, "project_id": payload.project_id}, {"_id": 0})
    if not farmer:
        return {"success": False, "message": "Farmer not found. Please JOIN first."}
    project = await db.projects.find_one({"project_id": payload.project_id}, {"_id": 0})
    if not project:
        return {"success": False, "message": "Project not found"}
    survival = project.get("survival_rate", 0.7)
    discount = project.get("conservative_discount", 0.2)
    est_credits = calculate_credits(payload.tree_count, payload.species, survival, discount)
    if project.get("payout_rule_type") == "per_tree":
        est_payout = round(payload.tree_count * project.get("payout_rate", 50), 2)
    else:
        est_payout = round(est_credits * project.get("payout_rate", 500), 2)
    activity_id = f"activity_{uuid.uuid4().hex[:10]}"
    doc = {
        "activity_id": activity_id,
        "farmer_id": farmer["farmer_id"],
        "farmer_name": farmer["name"],
        "farmer_phone": farmer["phone"],
        "project_id": payload.project_id,
        "project_name": project["name"],
        "tree_count": payload.tree_count,
        "species": payload.species,
        "planted_date": payload.planted_date,
        "lat": payload.lat,
        "lng": payload.lng,
        "photo_urls": payload.photo_urls,
        "notes": "",
        "status": "pending",
        "estimated_credits": est_credits,
        "estimated_payout": est_payout,
        "verifier_notes": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approved_at": None
    }
    await db.activities.insert_one(doc)
    await db.farmers.update_one({"farmer_id": farmer["farmer_id"]}, {"$inc": {"total_trees": payload.tree_count}})
    next_check = datetime.now(timezone.utc) + timedelta(days=project.get("monitoring_frequency_days", 90))
    return {
        "success": True,
        "message": "Activity received",
        "activity_id": activity_id,
        "estimated_payout": est_payout,
        "estimated_credits": est_credits,
        "next_check_date": next_check.strftime("%Y-%m-%d")
    }

@api_router.post("/webhook/status")
async def webhook_status(payload: WebhookStatusPayload):
    farmer = await db.farmers.find_one({"phone": payload.phone}, {"_id": 0})
    if not farmer:
        return {"success": False, "message": "Farmer not found"}
    activities = await db.activities.find({"farmer_id": farmer["farmer_id"]}, {"_id": 0}).sort("created_at", -1).to_list(10)
    return {
        "success": True,
        "farmer_name": farmer["name"],
        "total_trees": farmer.get("total_trees", 0),
        "approved_trees": farmer.get("approved_trees", 0),
        "estimated_credits": farmer.get("estimated_credits", 0),
        "total_payout": farmer.get("total_payout", 0),
        "recent_activities": [{"activity_id": a["activity_id"], "status": a["status"], "tree_count": a["tree_count"], "species": a["species"], "estimated_payout": a["estimated_payout"]} for a in activities]
    }

# ─── Export Endpoints ───

@api_router.get("/export/activity-csv")
async def export_activity_csv(request: Request, project_id: Optional[str] = None):
    user = await get_current_user(request)
    user_projects = await db.projects.find({"user_id": user["user_id"]}, {"_id": 0, "project_id": 1}).to_list(1000)
    project_ids = [p["project_id"] for p in user_projects]
    query = {"project_id": {"$in": project_ids}}
    if project_id:
        query["project_id"] = project_id
    activities = await db.activities.find(query, {"_id": 0}).to_list(10000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["farmer_id", "farmer_name", "phone", "activity_id", "lat", "lng", "planting_date", "species", "tree_count_submitted", "tree_count_approved", "verification_status", "verifier_notes", "evidence_photo_1_url", "evidence_photo_2_url", "estimated_credits", "estimated_payout", "created_at", "approved_at"])
    for a in activities:
        approved_trees = a["tree_count"] if a["status"] == "approved" else 0
        photos = a.get("photo_urls", [])
        writer.writerow([
            a.get("farmer_id", ""), a.get("farmer_name", ""), a.get("farmer_phone", ""),
            a.get("activity_id", ""), a.get("lat", ""), a.get("lng", ""), a.get("planted_date", ""),
            a.get("species", ""), a.get("tree_count", 0), approved_trees, a.get("status", ""),
            a.get("verifier_notes", ""), photos[0] if len(photos) > 0 else "", photos[1] if len(photos) > 1 else "",
            a.get("estimated_credits", 0), a.get("estimated_payout", 0), a.get("created_at", ""), a.get("approved_at", "")
        ])
    output.seek(0)
    return StreamingResponse(io.BytesIO(output.getvalue().encode()), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=activity_data.csv"})

@api_router.get("/export/payout-csv")
async def export_payout_csv(request: Request, project_id: Optional[str] = None):
    user = await get_current_user(request)
    user_projects = await db.projects.find({"user_id": user["user_id"]}, {"_id": 0, "project_id": 1}).to_list(1000)
    project_ids = [p["project_id"] for p in user_projects]
    query = {"project_id": {"$in": project_ids}}
    if project_id:
        query["project_id"] = project_id
    entries = await db.ledger.find(query, {"_id": 0}).to_list(10000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["farmer_id", "farmer_name", "phone", "upi_id", "project_id", "project_name", "approved_trees", "approved_credits_tCO2e", "payable_amount_INR", "paid_amount_INR", "balance_INR"])
    for e in entries:
        payable = round(e.get("payable_amount", 0), 2)
        paid = round(e.get("paid_amount", 0), 2)
        writer.writerow([
            e.get("farmer_id"), e.get("farmer_name"), e.get("farmer_phone"), e.get("upi_id", ""),
            e.get("project_id", ""), e.get("project_name", ""),
            e.get("approved_trees_total", 0), round(e.get("approved_credits_total", 0), 4),
            payable, paid, round(payable - paid, 2)
        ])
    output.seek(0)
    return StreamingResponse(io.BytesIO(output.getvalue().encode()), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=payout_ledger.csv"})

@api_router.get("/export/calculation-sheet")
async def export_calculation_sheet(request: Request, project_id: Optional[str] = None):
    user = await get_current_user(request)
    user_projects = await db.projects.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(1000)
    project_ids = [p["project_id"] for p in user_projects]
    query = {"project_id": {"$in": project_ids}}
    if project_id:
        query["project_id"] = project_id
    activities = await db.activities.find(query, {"_id": 0}).to_list(10000)
    projects_map = {p["project_id"]: p for p in user_projects}
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["activity_id", "species", "species_bucket", "sequestration_factor_tCO2_per_tree_per_year", "tree_count", "survival_rate", "conservative_discount", "formula", "estimated_tCO2e", "payout_rule", "payout_rate", "estimated_payout"])
    for a in activities:
        proj = projects_map.get(a.get("project_id"), {})
        bucket = get_species_bucket(a.get("species", ""))
        rate = SPECIES_RATES.get(bucket, 0.01)
        survival = proj.get("survival_rate", 0.7)
        discount = proj.get("conservative_discount", 0.2)
        formula = f"{a.get('tree_count',0)} x {rate} x {survival} x (1-{discount})"
        writer.writerow([a.get("activity_id"), a.get("species"), bucket, rate, a.get("tree_count", 0), survival, discount, formula, a.get("estimated_credits", 0), proj.get("payout_rule_type", "per_tree"), proj.get("payout_rate", 50), a.get("estimated_payout", 0)])
    output.seek(0)
    return StreamingResponse(io.BytesIO(output.getvalue().encode()), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=calculation_sheet.csv"})

@api_router.get("/export/dossier-pdf")
async def export_dossier_pdf(request: Request, project_id: Optional[str] = None):
    user = await get_current_user(request)
    all_projects = await db.projects.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(100)
    if project_id:
        projects = [p for p in all_projects if p["project_id"] == project_id]
    else:
        projects = all_projects
    if not projects:
        raise HTTPException(status_code=404, detail="No projects found")

    project_ids = [p["project_id"] for p in projects]
    farmers = await db.farmers.find({"project_id": {"$in": project_ids}}, {"_id": 0}).to_list(10000)
    activities = await db.activities.find({"project_id": {"$in": project_ids}}, {"_id": 0}).to_list(10000)
    approved = [a for a in activities if a["status"] == "approved"]

    def safe(text: str, max_len: int = 80) -> str:
        """Encode to Latin-1 safe string for FPDF Helvetica."""
        if not text:
            return ""
        return text.encode("latin-1", errors="replace").decode("latin-1")[:max_len]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ── Cover Page ──────────────────────────────────────────────
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 15, "VanaLedger - Project Dossier", ln=True, align="C")
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 8, "ESTIMATED UNITS - NOT ISSUED CREDITS", ln=True, align="C")
    pdf.cell(0, 8, f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", ln=True, align="C")
    pdf.ln(6)
    pdf.set_draw_color(26, 77, 46)
    pdf.set_line_width(0.8)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(8)

    # Portfolio summary if multiple projects
    if len(projects) > 1:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Portfolio Summary", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, f"  Total Projects : {len(projects)}", ln=True)
        pdf.cell(0, 7, f"  Total Farmers  : {len(farmers)}", ln=True)
        pdf.cell(0, 7, f"  Total Activities: {len(activities)}", ln=True)
        pdf.cell(0, 7, f"  Verified Activities: {len(approved)}", ln=True)
        total_trees = sum(a["tree_count"] for a in approved)
        total_credits = sum(a.get("estimated_credits", 0) for a in approved)
        total_payout = sum(a.get("estimated_payout", 0) for a in approved)
        pdf.cell(0, 7, f"  Approved Trees  : {total_trees:,}", ln=True)
        pdf.cell(0, 7, f"  Est. tCO2e      : {total_credits:.4f}", ln=True)
        pdf.cell(0, 7, f"  Est. Payout INR : {total_payout:,.2f}", ln=True)
        pdf.ln(8)

    # ── Per-Project Sections ────────────────────────────────────
    for proj in projects:
        pid = proj["project_id"]
        proj_farmers = [f for f in farmers if f["project_id"] == pid]
        proj_acts = [a for a in activities if a["project_id"] == pid]
        proj_approved = [a for a in proj_acts if a["status"] == "approved"]
        p_trees = sum(a["tree_count"] for a in proj_approved)
        p_credits = sum(a.get("estimated_credits", 0) for a in proj_approved)
        p_payout = sum(a.get("estimated_payout", 0) for a in proj_approved)

        if len(projects) > 1:
            pdf.add_page()

        pdf.set_font("Helvetica", "B", 16)
        pdf.set_fill_color(240, 248, 240)
        pdf.cell(0, 12, safe(f"Project: {proj.get('name', 'N/A')}"), ln=True, fill=True)
        pdf.ln(3)

        # 1. Project Details
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "1. Project Details", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, safe(f"  Project Name  : {proj.get('name', 'N/A')}"), ln=True)
        pdf.cell(0, 7, safe(f"  Region        : {proj.get('region', 'N/A')}"), ln=True)
        pdf.cell(0, 7, safe(f"  Status        : {proj.get('status', 'active').upper()}"), ln=True)
        pdf.cell(0, 7, f"  Created       : {str(proj.get('created_at', 'N/A'))[:10]}", ln=True)
        if proj.get("description"):
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, safe(f"  Description   : {proj['description']}", 200))
        pdf.ln(4)

        # 2. Species & Configuration
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "2. Species & Planting Configuration", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for s in proj.get("species_list", []):
            pdf.cell(0, 7, safe(f"  - {s.get('name', '').capitalize()}: {s.get('growth_rate', 'medium')} growth"), ln=True)
        pdf.cell(0, 7, f"  Max trees/acre   : {proj.get('max_trees_per_acre', 400)}", ln=True)
        pdf.cell(0, 7, f"  Monitoring every : {proj.get('monitoring_frequency_days', 90)} days", ln=True)
        pdf.ln(4)

        # 3. Credit Estimation Method
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "3. Credit Estimation Methodology", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, "  Formula: trees x seq_rate x survival x (1 - discount)", ln=True)
        pdf.cell(0, 7, f"  Survival rate        : {proj.get('survival_rate', 0.7)*100:.0f}%", ln=True)
        pdf.cell(0, 7, f"  Conservative discount: {proj.get('conservative_discount', 0.2)*100:.0f}%", ln=True)
        pdf.cell(0, 7, "  Species seq. rates   : Fast=0.02 | Medium=0.01 | Slow=0.005 tCO2/tree/yr", ln=True)
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(0, 6, "  DISCLAIMER: All values are estimates. Final issuance subject to third-party verification.")
        pdf.ln(4)

        # 4. Risk Controls
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "4. Risk Controls & Fraud Prevention", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, f"  Cooldown between activities : {proj.get('cooldown_days', 30)} days", ln=True)
        pdf.cell(0, 7, safe(f"  Required proofs             : {', '.join(proj.get('required_proofs', []))}"), ln=True)
        pdf.cell(0, 7, safe(f"  Payout rule                 : {proj.get('payout_rule_type', 'per_tree')} @ INR {proj.get('payout_rate', 50)}"), ln=True)
        pdf.ln(4)

        # 5. Monitoring Plan
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "5. Monitoring Plan", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, "  Survival checks at: 30, 90, and 365 days post-planting", ln=True)
        pdf.cell(0, 7, "  Evidence required : Geo-tagged photos + GPS pin", ln=True)
        pdf.cell(0, 7, f"  Monitoring cycle  : Every {proj.get('monitoring_frequency_days', 90)} days", ln=True)
        pdf.ln(4)

        # 6. Project Statistics
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "6. Project Statistics", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, f"  Farmers enrolled       : {len(proj_farmers)}", ln=True)
        pdf.cell(0, 7, f"  Total activities       : {len(proj_acts)}", ln=True)
        pdf.cell(0, 7, f"  Verified activities    : {len(proj_approved)}", ln=True)
        pdf.cell(0, 7, f"  Pending verification   : {len([a for a in proj_acts if a['status'] == 'pending'])}", ln=True)
        pdf.cell(0, 7, f"  Rejected activities    : {len([a for a in proj_acts if a['status'] == 'rejected'])}", ln=True)
        pdf.cell(0, 7, f"  Approved trees         : {p_trees:,}", ln=True)
        pdf.cell(0, 7, f"  Estimated tCO2e        : {p_credits:.4f}", ln=True)
        pdf.cell(0, 7, f"  Est. payout (INR)      : {p_payout:,.2f}", ln=True)
        pdf.ln(4)

        # 7. Farmer Summary Table
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, f"7. Farmer Roster ({min(len(proj_farmers), 15)} of {len(proj_farmers)} shown)", ln=True)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(230, 245, 230)
        pdf.cell(55, 7, "Name", border=1, fill=True)
        pdf.cell(32, 7, "Phone", border=1, fill=True)
        pdf.cell(22, 7, "Land Type", border=1, fill=True)
        pdf.cell(20, 7, "Acres", border=1, fill=True)
        pdf.cell(25, 7, "Appr. Trees", border=1, fill=True)
        pdf.cell(26, 7, "Est. tCO2e", border=1, ln=True, fill=True)
        pdf.set_font("Helvetica", "", 9)
        for f in proj_farmers[:15]:
            pdf.cell(55, 6, safe(str(f.get("name", "")), 30), border=1)
            pdf.cell(32, 6, safe(str(f.get("phone", ""))), border=1)
            pdf.cell(22, 6, safe(str(f.get("land_type", ""))), border=1)
            pdf.cell(20, 6, str(f.get("acres", "N/A")), border=1)
            pdf.cell(25, 6, str(f.get("approved_trees", 0)), border=1)
            pdf.cell(26, 6, f"{f.get('estimated_credits', 0):.4f}", border=1, ln=True)
        if len(proj_farmers) > 15:
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 6, f"  ... and {len(proj_farmers)-15} more farmers", ln=True)
        pdf.ln(4)

    # Final disclaimer
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Important Disclaimers", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 7,
        "All carbon credit values in this document are ESTIMATES based on rule-of-thumb "
        "calculations and have NOT been verified or certified by any registry.\n\n"
        "Final carbon credit issuance depends on:\n"
        "  1. Third-party field verification (DOE/VVB)\n"
        "  2. Registry approval (Verra VCS, Gold Standard, ICM, or other)\n"
        "  3. Actual survival rates at time of monitoring\n"
        "  4. Adherence to project methodology\n\n"
        "This document is generated from VanaLedger and is intended for internal "
        "planning and pre-verification purposes only."
    )

    pdf_bytes = pdf.output()
    proj_label = projects[0].get('name', '').replace(' ', '_') if len(projects) == 1 else "all_projects"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=project_dossier_{proj_label}.pdf"}
    )

@api_router.get("/export/evidence-json")
async def export_evidence_json(request: Request, project_id: Optional[str] = None):
    user = await get_current_user(request)
    user_projects = await db.projects.find({"user_id": user["user_id"]}, {"_id": 0, "project_id": 1}).to_list(1000)
    project_ids = [p["project_id"] for p in user_projects]
    query = {"project_id": {"$in": project_ids}}
    if project_id:
        query["project_id"] = project_id
    activities = await db.activities.find(query, {"_id": 0}).to_list(10000)
    evidence = []
    for a in activities:
        evidence.append({
            "activity_id": a["activity_id"],
            "lat": a.get("lat"),
            "lng": a.get("lng"),
            "photo_urls": a.get("photo_urls", []),
            "farmer_id": a["farmer_id"],
            "status": a["status"],
            "created_at": a.get("created_at")
        })
    output = json.dumps(evidence, indent=2)
    return StreamingResponse(io.BytesIO(output.encode()), media_type="application/json", headers={"Content-Disposition": "attachment; filename=evidence_pack.json"})

@api_router.get("/export/audit-log")
async def export_audit_log(request: Request, project_id: Optional[str] = None):
    user = await get_current_user(request)
    user_projects = await db.projects.find({"user_id": user["user_id"]}, {"_id": 0, "project_id": 1}).to_list(1000)
    project_ids = [p["project_id"] for p in user_projects]
    query = {"project_id": {"$in": project_ids}, "status": {"$in": ["approved", "rejected"]}}
    if project_id:
        query["project_id"] = project_id
    activities = await db.activities.find(query, {"_id": 0}).sort("approved_at", -1).to_list(10000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["activity_id", "project_id", "project_name", "farmer_id", "farmer_name", "farmer_phone", "species", "tree_count", "action", "verifier_notes", "approved_at", "created_at"])
    for a in activities:
        writer.writerow([
            a["activity_id"], a.get("project_id", ""), a.get("project_name", ""),
            a["farmer_id"], a.get("farmer_name", ""), a.get("farmer_phone", ""),
            a.get("species", ""), a["tree_count"],
            a["status"], a.get("verifier_notes", ""),
            a.get("approved_at", ""), a.get("created_at", "")
        ])
    output.seek(0)
    return StreamingResponse(io.BytesIO(output.getvalue().encode()), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=audit_log.csv"})

@api_router.get("/static/workflow")
async def serve_workflow_image():
    """Serve the VanaLedger workflow diagram PNG."""
    img_path = os.path.join(os.path.dirname(__file__), "static", "workflow.png")
    return FileResponse(img_path, media_type="image/png", filename="VanaLedger_Workflow.png")

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
