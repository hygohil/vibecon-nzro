from fastapi import FastAPI, APIRouter, HTTPException, Request, Response
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

class ProgramCreate(BaseModel):
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

class ProgramOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    program_id: str
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
    claims_count: int = 0
    created_at: Optional[str] = None

class FarmerCreate(BaseModel):
    name: str
    phone: str
    land_type: str = "owned"
    acres: Optional[float] = None
    upi_id: Optional[str] = None
    program_id: str

class FarmerOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    farmer_id: str
    name: str
    phone: str
    land_type: str = "owned"
    acres: Optional[float] = None
    upi_id: Optional[str] = None
    program_id: str
    program_name: Optional[str] = None
    status: str = "active"
    total_trees: int = 0
    approved_trees: int = 0
    estimated_credits: float = 0.0
    total_payout: float = 0.0
    created_at: Optional[str] = None

class ClaimCreate(BaseModel):
    farmer_id: str
    program_id: str
    tree_count: int
    species: str
    planted_date: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    photo_urls: List[str] = []
    notes: Optional[str] = ""

class ClaimOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    claim_id: str
    farmer_id: str
    farmer_name: Optional[str] = None
    farmer_phone: Optional[str] = None
    farmer_village: Optional[str] = None
    program_id: str
    program_name: Optional[str] = None
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

class ClaimAction(BaseModel):
    action: str
    verifier_notes: Optional[str] = ""

class WebhookJoinPayload(BaseModel):
    phone: str
    name: str
    village: str
    district: str
    land_type: str = "owned"
    acres: Optional[float] = None
    upi_id: Optional[str] = None
    program_id: str

class WebhookClaimPayload(BaseModel):
    phone: str
    program_id: str
    tree_count: int
    species: str
    planted_date: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    photo_urls: List[str] = []

class WebhookStatusPayload(BaseModel):
    phone: str

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

# ─── Programs ───

@api_router.post("/programs", response_model=ProgramOut)
async def create_program(program: ProgramCreate, request: Request):
    user = await get_current_user(request)
    doc = program.model_dump()
    doc["program_id"] = f"prog_{uuid.uuid4().hex[:10]}"
    doc["user_id"] = user["user_id"]
    doc["status"] = "active"
    doc["farmers_count"] = 0
    doc["claims_count"] = 0
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.programs.insert_one(doc)
    result = await db.programs.find_one({"program_id": doc["program_id"]}, {"_id": 0})
    return ProgramOut(**result)

@api_router.get("/programs", response_model=List[ProgramOut])
async def list_programs(request: Request):
    user = await get_current_user(request)
    programs = await db.programs.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(1000)
    for p in programs:
        p["farmers_count"] = await db.farmers.count_documents({"program_id": p["program_id"]})
        p["claims_count"] = await db.claims.count_documents({"program_id": p["program_id"]})
    return [ProgramOut(**p) for p in programs]

@api_router.get("/programs/{program_id}", response_model=ProgramOut)
async def get_program(program_id: str, request: Request):
    user = await get_current_user(request)
    p = await db.programs.find_one({"program_id": program_id, "user_id": user["user_id"]}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="Program not found")
    p["farmers_count"] = await db.farmers.count_documents({"program_id": program_id})
    p["claims_count"] = await db.claims.count_documents({"program_id": program_id})
    return ProgramOut(**p)

@api_router.delete("/programs/{program_id}")
async def delete_program(program_id: str, request: Request):
    user = await get_current_user(request)
    result = await db.programs.delete_one({"program_id": program_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Program not found")
    return {"message": "Program deleted"}

# ─── Farmers ───

@api_router.post("/farmers", response_model=FarmerOut)
async def create_farmer(farmer: FarmerCreate, request: Request):
    user = await get_current_user(request)
    program = await db.programs.find_one({"program_id": farmer.program_id, "user_id": user["user_id"]}, {"_id": 0})
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    doc = farmer.model_dump()
    doc["farmer_id"] = f"farmer_{uuid.uuid4().hex[:10]}"
    doc["program_name"] = program["name"]
    doc["status"] = "active"
    doc["total_trees"] = 0
    doc["approved_trees"] = 0
    doc["estimated_credits"] = 0.0
    doc["total_payout"] = 0.0
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.farmers.insert_one(doc)
    result = await db.farmers.find_one({"farmer_id": doc["farmer_id"]}, {"_id": 0})
    return FarmerOut(**result)

@api_router.get("/farmers", response_model=List[FarmerOut])
async def list_farmers(request: Request, program_id: Optional[str] = None):
    user = await get_current_user(request)
    user_programs = await db.programs.find({"user_id": user["user_id"]}, {"_id": 0, "program_id": 1}).to_list(1000)
    program_ids = [p["program_id"] for p in user_programs]
    query = {"program_id": {"$in": program_ids}}
    if program_id:
        query["program_id"] = program_id
    farmers = await db.farmers.find(query, {"_id": 0}).to_list(1000)
    return [FarmerOut(**f) for f in farmers]

@api_router.get("/farmers/{farmer_id}", response_model=FarmerOut)
async def get_farmer(farmer_id: str, request: Request):
    _ = await get_current_user(request)  # Authentication check
    farmer = await db.farmers.find_one({"farmer_id": farmer_id}, {"_id": 0})
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return FarmerOut(**farmer)

# ─── Claims ───

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

@api_router.post("/claims", response_model=ClaimOut)
async def create_claim(claim: ClaimCreate, request: Request):
    _ = await get_current_user(request)  # Authentication check
    program = await db.programs.find_one({"program_id": claim.program_id}, {"_id": 0})
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    farmer = await db.farmers.find_one({"farmer_id": claim.farmer_id}, {"_id": 0})
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    survival = program.get("survival_rate", 0.7)
    discount = program.get("conservative_discount", 0.2)
    est_credits = calculate_credits(claim.tree_count, claim.species, survival, discount)
    if program.get("payout_rule_type") == "per_tree":
        est_payout = round(claim.tree_count * program.get("payout_rate", 50), 2)
    else:
        est_payout = round(est_credits * program.get("payout_rate", 500), 2)
    doc = claim.model_dump()
    doc["claim_id"] = f"claim_{uuid.uuid4().hex[:10]}"
    doc["farmer_name"] = farmer.get("name")
    doc["farmer_phone"] = farmer.get("phone")
    doc["farmer_village"] = farmer.get("village")
    doc["program_name"] = program.get("name")
    doc["status"] = "pending"
    doc["estimated_credits"] = est_credits
    doc["estimated_payout"] = est_payout
    doc["verifier_notes"] = ""
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    doc["approved_at"] = None
    await db.claims.insert_one(doc)
    await db.farmers.update_one({"farmer_id": claim.farmer_id}, {"$inc": {"total_trees": claim.tree_count}})
    result = await db.claims.find_one({"claim_id": doc["claim_id"]}, {"_id": 0})
    return ClaimOut(**result)

@api_router.get("/claims", response_model=List[ClaimOut])
async def list_claims(request: Request, program_id: Optional[str] = None, status: Optional[str] = None):
    user = await get_current_user(request)
    user_programs = await db.programs.find({"user_id": user["user_id"]}, {"_id": 0, "program_id": 1}).to_list(1000)
    program_ids = [p["program_id"] for p in user_programs]
    query = {"program_id": {"$in": program_ids}}
    if program_id:
        query["program_id"] = program_id
    if status:
        query["status"] = status
    claims = await db.claims.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [ClaimOut(**c) for c in claims]

@api_router.put("/claims/{claim_id}/action")
async def action_claim(claim_id: str, action: ClaimAction, request: Request):
    _ = await get_current_user(request)  # Authentication check
    claim = await db.claims.find_one({"claim_id": claim_id}, {"_id": 0})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if action.action == "approve":
        new_status = "approved"
        approved_at = datetime.now(timezone.utc).isoformat()
        await db.claims.update_one({"claim_id": claim_id}, {"$set": {"status": new_status, "verifier_notes": action.verifier_notes, "approved_at": approved_at}})
        await db.farmers.update_one({"farmer_id": claim["farmer_id"]}, {"$inc": {"approved_trees": claim["tree_count"], "estimated_credits": claim["estimated_credits"], "total_payout": claim["estimated_payout"]}})
        existing = await db.ledger.find_one({"farmer_id": claim["farmer_id"]}, {"_id": 0})
        if existing:
            await db.ledger.update_one({"farmer_id": claim["farmer_id"]}, {"$inc": {"approved_trees_total": claim["tree_count"], "approved_credits_total": claim["estimated_credits"], "payable_amount": claim["estimated_payout"]}})
        else:
            farmer = await db.farmers.find_one({"farmer_id": claim["farmer_id"]}, {"_id": 0})
            await db.ledger.insert_one({
                "ledger_id": f"ledger_{uuid.uuid4().hex[:10]}",
                "farmer_id": claim["farmer_id"],
                "farmer_name": farmer.get("name", ""),
                "farmer_phone": farmer.get("phone", ""),
                "farmer_village": farmer.get("village", ""),
                "upi_id": farmer.get("upi_id", ""),
                "program_id": claim["program_id"],
                "approved_trees_total": claim["tree_count"],
                "approved_credits_total": claim["estimated_credits"],
                "payable_amount": claim["estimated_payout"],
                "paid_amount": 0.0,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
    elif action.action == "reject":
        await db.claims.update_one({"claim_id": claim_id}, {"$set": {"status": "rejected", "verifier_notes": action.verifier_notes}})
    elif action.action == "needs_info":
        await db.claims.update_one({"claim_id": claim_id}, {"$set": {"status": "needs_info", "verifier_notes": action.verifier_notes}})
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    updated = await db.claims.find_one({"claim_id": claim_id}, {"_id": 0})
    return updated

# ─── Ledger ───

@api_router.get("/ledger")
async def get_ledger(request: Request, program_id: Optional[str] = None):
    user = await get_current_user(request)
    user_programs = await db.programs.find({"user_id": user["user_id"]}, {"_id": 0, "program_id": 1}).to_list(1000)
    program_ids = [p["program_id"] for p in user_programs]
    query = {"program_id": {"$in": program_ids}}
    if program_id:
        query["program_id"] = program_id
    ledger_entries = await db.ledger.find(query, {"_id": 0}).to_list(1000)
    return ledger_entries

# ─── Dashboard Stats ───

@api_router.get("/dashboard/stats")
async def dashboard_stats(request: Request):
    user = await get_current_user(request)
    user_programs = await db.programs.find({"user_id": user["user_id"]}, {"_id": 0, "program_id": 1, "name": 1}).to_list(1000)
    program_ids = [p["program_id"] for p in user_programs]
    total_programs = len(program_ids)
    total_farmers = await db.farmers.count_documents({"program_id": {"$in": program_ids}})
    total_claims = await db.claims.count_documents({"program_id": {"$in": program_ids}})
    pending_claims = await db.claims.count_documents({"program_id": {"$in": program_ids}, "status": "pending"})
    approved_claims = await db.claims.count_documents({"program_id": {"$in": program_ids}, "status": "approved"})
    pipeline = [
        {"$match": {"program_id": {"$in": program_ids}, "status": "approved"}},
        {"$group": {"_id": None, "total_trees": {"$sum": "$tree_count"}, "total_credits": {"$sum": "$estimated_credits"}, "total_payout": {"$sum": "$estimated_payout"}}}
    ]
    agg = await db.claims.aggregate(pipeline).to_list(1)
    totals = agg[0] if agg else {"total_trees": 0, "total_credits": 0, "total_payout": 0}
    recent_claims = await db.claims.find({"program_id": {"$in": program_ids}}, {"_id": 0}).sort("created_at", -1).to_list(5)
    return {
        "total_programs": total_programs,
        "total_farmers": total_farmers,
        "total_claims": total_claims,
        "pending_claims": pending_claims,
        "approved_claims": approved_claims,
        "approved_trees": totals.get("total_trees", 0),
        "estimated_credits": round(totals.get("total_credits", 0), 4),
        "total_payout": round(totals.get("total_payout", 0), 2),
        "recent_claims": recent_claims
    }

# ─── WhatsApp Webhook Endpoints ───

@api_router.post("/webhook/join")
async def webhook_join(payload: WebhookJoinPayload):
    program = await db.programs.find_one({"program_id": payload.program_id}, {"_id": 0})
    if not program:
        return {"success": False, "message": "Program not found"}
    existing = await db.farmers.find_one({"phone": payload.phone, "program_id": payload.program_id}, {"_id": 0})
    if existing:
        return {"success": True, "message": f"Already enrolled in {program['name']}", "farmer_id": existing["farmer_id"]}
    farmer_id = f"farmer_{uuid.uuid4().hex[:10]}"
    doc = {
        "farmer_id": farmer_id,
        "name": payload.name,
        "phone": payload.phone,
        "village": payload.village,
        "district": payload.district,
        "land_type": payload.land_type,
        "acres": payload.acres,
        "upi_id": payload.upi_id,
        "program_id": payload.program_id,
        "program_name": program["name"],
        "status": "active",
        "total_trees": 0,
        "approved_trees": 0,
        "estimated_credits": 0.0,
        "total_payout": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.farmers.insert_one(doc)
    return {"success": True, "message": f"Enrolled in {program['name']}", "farmer_id": farmer_id}

@api_router.post("/webhook/claim")
async def webhook_claim(payload: WebhookClaimPayload):
    farmer = await db.farmers.find_one({"phone": payload.phone, "program_id": payload.program_id}, {"_id": 0})
    if not farmer:
        return {"success": False, "message": "Farmer not found. Please JOIN first."}
    program = await db.programs.find_one({"program_id": payload.program_id}, {"_id": 0})
    if not program:
        return {"success": False, "message": "Program not found"}
    survival = program.get("survival_rate", 0.7)
    discount = program.get("conservative_discount", 0.2)
    est_credits = calculate_credits(payload.tree_count, payload.species, survival, discount)
    if program.get("payout_rule_type") == "per_tree":
        est_payout = round(payload.tree_count * program.get("payout_rate", 50), 2)
    else:
        est_payout = round(est_credits * program.get("payout_rate", 500), 2)
    claim_id = f"claim_{uuid.uuid4().hex[:10]}"
    doc = {
        "claim_id": claim_id,
        "farmer_id": farmer["farmer_id"],
        "farmer_name": farmer["name"],
        "farmer_phone": farmer["phone"],
        "farmer_village": farmer.get("village", ""),
        "program_id": payload.program_id,
        "program_name": program["name"],
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
    await db.claims.insert_one(doc)
    await db.farmers.update_one({"farmer_id": farmer["farmer_id"]}, {"$inc": {"total_trees": payload.tree_count}})
    next_check = datetime.now(timezone.utc) + timedelta(days=program.get("monitoring_frequency_days", 90))
    return {
        "success": True,
        "message": "Claim received",
        "claim_id": claim_id,
        "estimated_payout": est_payout,
        "estimated_credits": est_credits,
        "next_check_date": next_check.strftime("%Y-%m-%d")
    }

@api_router.post("/webhook/status")
async def webhook_status(payload: WebhookStatusPayload):
    farmer = await db.farmers.find_one({"phone": payload.phone}, {"_id": 0})
    if not farmer:
        return {"success": False, "message": "Farmer not found"}
    claims = await db.claims.find({"farmer_id": farmer["farmer_id"]}, {"_id": 0}).sort("created_at", -1).to_list(10)
    return {
        "success": True,
        "farmer_name": farmer["name"],
        "total_trees": farmer.get("total_trees", 0),
        "approved_trees": farmer.get("approved_trees", 0),
        "estimated_credits": farmer.get("estimated_credits", 0),
        "total_payout": farmer.get("total_payout", 0),
        "recent_claims": [{"claim_id": c["claim_id"], "status": c["status"], "tree_count": c["tree_count"], "species": c["species"], "estimated_payout": c["estimated_payout"]} for c in claims]
    }

# ─── Export Endpoints ───

@api_router.get("/export/activity-csv")
async def export_activity_csv(request: Request, program_id: Optional[str] = None):
    user = await get_current_user(request)
    user_programs = await db.programs.find({"user_id": user["user_id"]}, {"_id": 0, "program_id": 1}).to_list(1000)
    program_ids = [p["program_id"] for p in user_programs]
    query = {"program_id": {"$in": program_ids}}
    if program_id:
        query["program_id"] = program_id
    claims = await db.claims.find(query, {"_id": 0}).to_list(10000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["farmer_id", "farmer_name", "phone", "village", "claim_id", "lat", "lng", "planting_date", "species", "tree_count_submitted", "tree_count_approved", "verification_status", "verifier_notes", "evidence_photo_1_url", "evidence_photo_2_url", "estimated_credits", "estimated_payout", "created_at", "approved_at"])
    for c in claims:
        approved_trees = c["tree_count"] if c["status"] == "approved" else 0
        photos = c.get("photo_urls", [])
        writer.writerow([
            c.get("farmer_id", ""), c.get("farmer_name", ""), c.get("farmer_phone", ""), c.get("farmer_village", ""),
            c.get("claim_id", ""), c.get("lat", ""), c.get("lng", ""), c.get("planted_date", ""),
            c.get("species", ""), c.get("tree_count", 0), approved_trees, c.get("status", ""),
            c.get("verifier_notes", ""), photos[0] if len(photos) > 0 else "", photos[1] if len(photos) > 1 else "",
            c.get("estimated_credits", 0), c.get("estimated_payout", 0), c.get("created_at", ""), c.get("approved_at", "")
        ])
    output.seek(0)
    return StreamingResponse(io.BytesIO(output.getvalue().encode()), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=activity_data.csv"})

@api_router.get("/export/payout-csv")
async def export_payout_csv(request: Request, program_id: Optional[str] = None):
    user = await get_current_user(request)
    user_programs = await db.programs.find({"user_id": user["user_id"]}, {"_id": 0, "program_id": 1}).to_list(1000)
    program_ids = [p["program_id"] for p in user_programs]
    query = {"program_id": {"$in": program_ids}}
    if program_id:
        query["program_id"] = program_id
    entries = await db.ledger.find(query, {"_id": 0}).to_list(10000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["farmer_id", "farmer_name", "phone", "village", "upi_id", "approved_trees", "approved_credits_tCO2e", "payable_amount_INR", "paid_amount_INR"])
    for e in entries:
        writer.writerow([e.get("farmer_id"), e.get("farmer_name"), e.get("farmer_phone"), e.get("farmer_village"), e.get("upi_id", ""), e.get("approved_trees_total", 0), round(e.get("approved_credits_total", 0), 4), round(e.get("payable_amount", 0), 2), round(e.get("paid_amount", 0), 2)])
    output.seek(0)
    return StreamingResponse(io.BytesIO(output.getvalue().encode()), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=payout_ledger.csv"})

@api_router.get("/export/calculation-sheet")
async def export_calculation_sheet(request: Request, program_id: Optional[str] = None):
    user = await get_current_user(request)
    user_programs = await db.programs.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(1000)
    program_ids = [p["program_id"] for p in user_programs]
    query = {"program_id": {"$in": program_ids}}
    if program_id:
        query["program_id"] = program_id
    claims = await db.claims.find(query, {"_id": 0}).to_list(10000)
    programs_map = {p["program_id"]: p for p in user_programs}
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["claim_id", "species", "species_bucket", "sequestration_factor_tCO2_per_tree_per_year", "tree_count", "survival_rate", "conservative_discount", "formula", "estimated_tCO2e", "payout_rule", "payout_rate", "estimated_payout"])
    for c in claims:
        prog = programs_map.get(c.get("program_id"), {})
        bucket = get_species_bucket(c.get("species", ""))
        rate = SPECIES_RATES.get(bucket, 0.01)
        survival = prog.get("survival_rate", 0.7)
        discount = prog.get("conservative_discount", 0.2)
        formula = f"{c.get('tree_count',0)} x {rate} x {survival} x (1-{discount})"
        writer.writerow([c.get("claim_id"), c.get("species"), bucket, rate, c.get("tree_count", 0), survival, discount, formula, c.get("estimated_credits", 0), prog.get("payout_rule_type", "per_tree"), prog.get("payout_rate", 50), c.get("estimated_payout", 0)])
    output.seek(0)
    return StreamingResponse(io.BytesIO(output.getvalue().encode()), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=calculation_sheet.csv"})

@api_router.get("/export/dossier-pdf")
async def export_dossier_pdf(request: Request, program_id: Optional[str] = None):
    user = await get_current_user(request)
    programs = await db.programs.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(100)
    if program_id:
        programs = [p for p in programs if p["program_id"] == program_id]
    if not programs:
        raise HTTPException(status_code=404, detail="No programs found")
    prog = programs[0]
    program_ids = [p["program_id"] for p in programs]
    farmers = await db.farmers.find({"program_id": {"$in": program_ids}}, {"_id": 0}).to_list(10000)
    claims = await db.claims.find({"program_id": {"$in": program_ids}}, {"_id": 0}).to_list(10000)
    approved = [c for c in claims if c["status"] == "approved"]
    total_trees = sum(c["tree_count"] for c in approved)
    total_credits = sum(c.get("estimated_credits", 0) for c in approved)
    total_payout = sum(c.get("estimated_payout", 0) for c in approved)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, "Project Dossier", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, "ESTIMATED UNITS - NOT ISSUED CREDITS", ln=True, align="C")
    pdf.cell(0, 8, f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "1. Program Details", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Program Name: {prog.get('name', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Region: {prog.get('region', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Description: {prog.get('description', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Status: {prog.get('status', 'active')}", ln=True)
    pdf.cell(0, 7, f"Created: {prog.get('created_at', 'N/A')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "2. Species & Planting Configuration", ln=True)
    pdf.set_font("Helvetica", "", 11)
    species = prog.get("species_list", [])
    if species:
        for s in species:
            pdf.cell(0, 7, f"  - {s.get('name', 'Unknown')}: {s.get('growth_rate', 'medium')} growth", ln=True)
    else:
        pdf.cell(0, 7, "  Species configured at claim level", ln=True)
    pdf.cell(0, 7, f"  Monitoring frequency: Every {prog.get('monitoring_frequency_days', 90)} days", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "3. Credit Estimation Method", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, "Formula: tree_count x sequestration_rate x survival_rate x (1 - discount)", ln=True)
    pdf.cell(0, 7, f"  Survival rate: {prog.get('survival_rate', 0.7)*100:.0f}%", ln=True)
    pdf.cell(0, 7, f"  Conservative discount: {prog.get('conservative_discount', 0.2)*100:.0f}%", ln=True)
    pdf.cell(0, 7, "  Species rates: Fast=0.02, Medium=0.01, Slow=0.005 tCO2/tree/year", ln=True)
    pdf.cell(0, 7, "  DISCLAIMER: These are estimated units, not issued/certified credits.", ln=True)
    pdf.cell(0, 7, "  Final issuance depends on verification + registry rules.", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "4. Risk Controls & Fraud Prevention", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"  Max trees per acre: {prog.get('max_trees_per_acre', 400)}", ln=True)
    pdf.cell(0, 7, f"  Cooldown between claims: {prog.get('cooldown_days', 30)} days", ln=True)
    pdf.cell(0, 7, f"  Required proofs: {', '.join(prog.get('required_proofs', []))}", ln=True)
    pdf.cell(0, 7, f"  Payout rule: {prog.get('payout_rule_type', 'per_tree')} @ INR {prog.get('payout_rate', 50)}", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "5. Monitoring Plan", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, "  Survival check at: 30, 90, 365 days post-planting", ln=True)
    pdf.cell(0, 7, "  Evidence: Geo-tagged photos + location pin", ln=True)
    pdf.cell(0, 7, f"  Monitoring frequency: {prog.get('monitoring_frequency_days', 90)} days", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "6. Summary Statistics", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"  Farmers enrolled: {len(farmers)}", ln=True)
    pdf.cell(0, 7, f"  Total claims: {len(claims)}", ln=True)
    pdf.cell(0, 7, f"  Approved claims: {len(approved)}", ln=True)
    pdf.cell(0, 7, f"  Approved trees: {total_trees}", ln=True)
    pdf.cell(0, 7, f"  Estimated tCO2e: {total_credits:.4f}", ln=True)
    pdf.cell(0, 7, f"  Total estimated payout: INR {total_payout:.2f}", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "7. Geography & Villages", ln=True)
    pdf.set_font("Helvetica", "", 11)
    villages = list(set(f.get("village", "") for f in farmers if f.get("village")))
    districts = list(set(f.get("district", "") for f in farmers if f.get("district")))
    pdf.cell(0, 7, f"  Districts: {', '.join(districts) if districts else 'N/A'}", ln=True)
    pdf.cell(0, 7, f"  Villages: {', '.join(villages[:20]) if villages else 'N/A'}", ln=True)
    pdf_bytes = pdf.output()
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=project_dossier_{prog.get('name','').replace(' ','_')}.pdf"})

@api_router.get("/export/evidence-json")
async def export_evidence_json(request: Request, program_id: Optional[str] = None):
    user = await get_current_user(request)
    user_programs = await db.programs.find({"user_id": user["user_id"]}, {"_id": 0, "program_id": 1}).to_list(1000)
    program_ids = [p["program_id"] for p in user_programs]
    query = {"program_id": {"$in": program_ids}}
    if program_id:
        query["program_id"] = program_id
    claims = await db.claims.find(query, {"_id": 0}).to_list(10000)
    evidence = []
    for c in claims:
        evidence.append({
            "claim_id": c["claim_id"],
            "lat": c.get("lat"),
            "lng": c.get("lng"),
            "photo_urls": c.get("photo_urls", []),
            "farmer_id": c["farmer_id"],
            "status": c["status"],
            "created_at": c.get("created_at")
        })
    output = json.dumps(evidence, indent=2)
    return StreamingResponse(io.BytesIO(output.encode()), media_type="application/json", headers={"Content-Disposition": "attachment; filename=evidence_pack.json"})

@api_router.get("/export/audit-log")
async def export_audit_log(request: Request, program_id: Optional[str] = None):
    user = await get_current_user(request)
    user_programs = await db.programs.find({"user_id": user["user_id"]}, {"_id": 0, "program_id": 1}).to_list(1000)
    program_ids = [p["program_id"] for p in user_programs]
    query = {"program_id": {"$in": program_ids}, "status": {"$in": ["approved", "rejected"]}}
    if program_id:
        query["program_id"] = program_id
    claims = await db.claims.find(query, {"_id": 0}).to_list(10000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["claim_id", "action", "verifier_notes", "approved_at", "farmer_id", "tree_count"])
    for c in claims:
        writer.writerow([c["claim_id"], c["status"], c.get("verifier_notes", ""), c.get("approved_at", ""), c["farmer_id"], c["tree_count"]])
    output.seek(0)
    return StreamingResponse(io.BytesIO(output.getvalue().encode()), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=audit_log.csv"})

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
