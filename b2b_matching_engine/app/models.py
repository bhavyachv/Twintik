"""
MongoDB models serialization helpers.
Since MongoDB is schema-flexible, we do not use SQLAlchemy or ODM models.
We define helper functions to map raw MongoDB documents to API-friendly response dictionaries.
"""
from typing import Dict, Any

def company_doc_to_response(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts a raw MongoDB company document into a JSON-safe response dict.
    Converts ObjectId to string, renames _id to id, and excludes the vector_embedding.
    """
    if not document:
        return {}
    
    response = dict(document)
    if "_id" in response:
        response["id"] = str(response["_id"])
        del response["_id"]
        
    # Exclude raw vector embedding from standard response to save bandwidth
    response.pop("vector_embedding", None)
        
    return response
