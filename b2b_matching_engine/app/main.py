import os
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query, Header, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId

from app.database import connect_to_mongo, close_mongo_connection, companies_collection
from app.schemas import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    SearchRequest,
    SearchResult
)
from app.utils import validate_object_id, company_doc_to_response
from app.embedding_service import generate_and_save_company_embedding
from app.recommendation_service import search_companies
from app.seed_data import seed_data

app = FastAPI(
    title="Twintik B2B Matching Engine",
    description="FastAPI + MongoDB Two-Stage Recommendation Engine",
    version="1.0.0"
)

# Enable CORS for local cross-origin calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()
    global companies_collection
    import app.database
    companies_collection = app.database.companies_collection

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# Static files folder setting
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Spec endpoint: GET /
@app.get("/")
async def root(accept: Optional[str] = Header(None)):
    """
    Returns API running status JSON. If accessed by a browser requesting HTML,
    serves the frontend dashboard UI index.html instead.
    """
    if accept and "text/html" in accept:
        static_file = os.path.join(static_dir, "index.html")
        if os.path.exists(static_file):
            return FileResponse(static_file)
    return {"message": "Twintik B2B Matching Engine with MongoDB is running"}

# Spec endpoint: POST /companies
@app.post("/companies", response_model=CompanyResponse, status_code=210)
async def create_company(company: CompanyCreate, background_tasks: BackgroundTasks):
    """
    Create a company profile. Add timestamps. Insert into MongoDB.
    Trigger embedding generation in BackgroundTasks. Return created company.
    """
    # Check if company name already exists (enforcing uniqueness constraint)
    existing = await companies_collection.find_one({"company_name": company.company_name})
    if existing:
        raise HTTPException(status_code=400, detail="Company name already exists")
        
    doc = company.dict()
    now = datetime.now(timezone.utc)
    doc["created_at"] = now
    doc["updated_at"] = now
    doc["vector_embedding"] = None  # Will be generated asynchronously
    
    result = await companies_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    
    # Trigger vector embedding calculation in background task
    background_tasks.add_task(generate_and_save_company_embedding, str(result.inserted_id))
    
    # Return formatted response
    return company_doc_to_response(doc)

# Spec endpoint: GET /companies
@app.get("/companies", response_model=List[CompanyResponse])
async def list_companies(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=1000),
    country: Optional[str] = None,
    primary_industry: Optional[str] = None,
    city: Optional[str] = None
):
    """
    Return paginated company list with optional filters.
    """
    skip = (page - 1) * limit
    query = {}
    if country:
        query["country"] = country
    if primary_industry:
        query["primary_industry"] = primary_industry
    if city:
        query["city"] = city
        
    cursor = companies_collection.find(query).skip(skip).limit(limit)
    companies = await cursor.to_list(length=limit)
    return [company_doc_to_response(c) for c in companies]

# Spec endpoint: GET /companies/{company_id}
@app.get("/companies/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: str):
    """
    Return company details by MongoDB ObjectId.
    """
    obj_id = validate_object_id(company_id)
    company = await companies_collection.find_one({"_id": obj_id})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company_doc_to_response(company)

# Spec endpoint: PATCH /companies/{company_id}
@app.patch("/companies/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    company_update: CompanyUpdate,
    background_tasks: BackgroundTasks
):
    """
    Update company profile. Update updated_at timestamp.
    Trigger embedding regeneration in BackgroundTasks. Return updated company.
    """
    obj_id = validate_object_id(company_id)
    existing = await companies_collection.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Company not found")
        
    update_data = company_update.dict(exclude_none=True)
    if not update_data:
        return company_doc_to_response(existing)
        
    # Enforce uniqueness of company name if it is being changed
    if "company_name" in update_data and update_data["company_name"] != existing["company_name"]:
        name_exists = await companies_collection.find_one({"company_name": update_data["company_name"]})
        if name_exists:
            raise HTTPException(status_code=400, detail="Company name already exists")
            
    now = datetime.now(timezone.utc)
    update_data["updated_at"] = now
    
    await companies_collection.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )
    
    # Fetch latest copy from database
    updated_company = await companies_collection.find_one({"_id": obj_id})
    
    # Trigger embedding regeneration in background task if any semantic field changed
    semantic_fields = {"company_bio", "core_team_designations", "specialties", "product_service_offerings"}
    if any(field in update_data for field in semantic_fields):
        background_tasks.add_task(generate_and_save_company_embedding, company_id)
        
    return company_doc_to_response(updated_company)

# Spec endpoint: POST /search
@app.post("/search", response_model=List[SearchResult])
async def search(search_request: SearchRequest):
    """
    Run the two-stage B2B recommendation engine.
    Returns matched and ranked companies as JSON array.
    """
    try:
        results = await search_companies(search_request)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation engine failed: {str(e)}")

# Spec endpoint: POST /admin/regenerate-embeddings
@app.post("/admin/regenerate-embeddings")
async def regenerate_all_embeddings(background_tasks: BackgroundTasks):
    """
    Regenerate vector embeddings for all companies.
    """
    cursor = companies_collection.find({}, {"_id": 1})
    companies = await cursor.to_list(length=2000)
    for company in companies:
        background_tasks.add_task(generate_and_save_company_embedding, str(company["_id"]))
    return {"message": f"Queued embedding regeneration for {len(companies)} companies"}

# UI Helper endpoint: POST /admin/seed
@app.post("/admin/seed")
async def seed_database_api():
    """
    Seeding route to pre-populate database from the UI console.
    """
    try:
        await seed_data()
        return {"message": "Database seeded successfully with unique companies."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database seeding failed: {str(e)}")

# Mount static files folder to serve CSS, JS, and images
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
