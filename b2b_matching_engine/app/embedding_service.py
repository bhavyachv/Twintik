import os
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from bson import ObjectId
from datetime import datetime, timezone

# Load model globally (once on startup)
print("Initializing SentenceTransformer model 'all-MiniLM-L6-v2' globally...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("SentenceTransformer model loaded successfully.")

def build_company_context(company: Dict[str, Any]) -> str:
    """
    Builds context string for generating B2B recommendation embeddings.
    Format:
    Bio: {company_bio}. Offerings: {product_service_offerings}. Specialties: {specialties}. Core Team: {core_team_designations}.
    """
    bio = company.get("company_bio") or ""
    offerings = company.get("product_service_offerings") or ""
    specialties = company.get("specialties") or ""
    team = company.get("core_team_designations") or ""
    
    parts = []
    if bio:
        parts.append(f"Bio: {bio.strip()}")
    if offerings:
        parts.append(f"Offerings: {offerings.strip()}")
    if specialties:
        parts.append(f"Specialties: {specialties.strip()}")
    if team:
        parts.append(f"Core Team: {team.strip()}")
        
    # Standardize spaces and periods
    joined = ". ".join(parts)
    if not joined.endswith("."):
        joined += "."
    return joined

def generate_embedding(text: str) -> List[float]:
    """
    Converts a search context string into a 384-dimension list of floats.
    """
    if not text.strip():
        # Handle empty context gracefully
        return [0.0] * 384
    
    # Generate embeddings and convert numpy array to list of floats
    embedding = model.encode(text)
    return embedding.tolist()

async def generate_and_save_company_embedding(company_id: str):
    """
    Async background task helper to build context, generate vector embeddings,
    and save them directly to the company document in MongoDB.
    """
    from app.database import companies_collection
    
    try:
        obj_id = ObjectId(company_id)
        company = await companies_collection.find_one({"_id": obj_id})
        if not company:
            print(f"Error: Company {company_id} not found in database.")
            return
            
        context = build_company_context(company)
        embedding = generate_embedding(context)
        
        now = datetime.now(timezone.utc)
        await companies_collection.update_one(
            {"_id": obj_id},
            {
                "$set": {
                    "vector_embedding": embedding,
                    "updated_at": now
                }
            }
        )
        print(f"Success: Generated and saved embedding vector for company {company.get('company_name')} ({company_id}).")
    except Exception as e:
        print(f"Exception while generating embedding for company {company_id}: {str(e)}")
