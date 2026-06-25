from bson import ObjectId
from fastapi import HTTPException
from typing import Any, Dict

def object_id_to_str(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts '_id' field of a MongoDB document to a string key 'id'.
    """
    if not document:
        return document
    
    new_doc = dict(document)
    if "_id" in new_doc:
        new_doc["id"] = str(new_doc["_id"])
        del new_doc["_id"]
    return new_doc

def company_doc_to_response(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts a raw MongoDB company document into a JSON-safe response dict.
    Excludes the vector_embedding and translates ObjectId to string.
    """
    if not document:
        return {}
    
    response = dict(document)
    if "_id" in response:
        response["id"] = str(response["_id"])
        del response["_id"]
        
    response.pop("vector_embedding", None)
    return response

def validate_object_id(id_str: str) -> ObjectId:
    """
    Validates a string format of MongoDB ObjectId and returns ObjectId instance.
    Raises HTTP 400 Bad Request error if the format is invalid.
    """
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid MongoDB ObjectId format"
        )
