import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from pymongo.uri_parser import parse_uri

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "b2b_profiles")

client = None
db = None
companies_collection = None

async def connect_to_mongo():
    global client, db, companies_collection
    print(f"Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URL)
    
    # Parse database name from URL if possible
    try:
        parsed_uri = parse_uri(MONGODB_URL)
        uri_db = parsed_uri.get("database")
    except Exception:
        uri_db = None
        
    db_name = DATABASE_NAME or uri_db or "twintik_b2b"
    print(f"Selecting database: '{db_name}'")
    db = client[db_name]
    companies_collection = db[COLLECTION_NAME]
    
    # Ensure startup indexes are created
    print(f"Creating indexes on '{companies_collection.name}' collection...")
    await companies_collection.create_index("company_name", unique=True)
    await companies_collection.create_index("country")
    await companies_collection.create_index("city")
    await companies_collection.create_index("primary_industry")
    await companies_collection.create_index("funding_stage")
    await companies_collection.create_index("is_verified_business")
    await companies_collection.create_index("business_type")
    await companies_collection.create_index("min_order_qty")
    print("Indexes created successfully.")

async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("MongoDB connection closed.")
