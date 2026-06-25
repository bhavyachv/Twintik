import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any

import app.database as db
from app.schemas import SearchRequest
from app.embedding_service import generate_embedding

async def search_companies(search_request: SearchRequest) -> List[Dict[str, Any]]:
    """
    Two-stage B2B recommendation query:
    1. Partial heuristic hard-filtering (>= 50% filter match) in Python
    2. Semantic vector ranking using Sentence-Transformers and Scikit-Learn
    """
    # Fetch ALL companies that have precomputed embeddings
    mongo_filter = {
        "vector_embedding": {"$exists": True, "$ne": None}
    }
    cursor = db.companies_collection.find(mongo_filter)
    all_candidates = await cursor.to_list(length=2000)

    if not all_candidates:
        return []

    # Stage 1: Strict Hard-Filter Matching (100% of user's active filters must match)
    if search_request.filters:
        filters_dict = search_request.filters.dict(exclude_none=True)
        if filters_dict:
            filtered_candidates = []

            for company in all_candidates:
                matches_all = True

                for key, val in filters_dict.items():
                    if key == "min_order_qty":
                        # MOQ: company's MOQ should be <= the user's requested max
                        if company.get("min_order_qty", float('inf')) > val:
                            matches_all = False
                            break
                    elif key == "is_verified_business":
                        # Boolean: exact match
                        if company.get("is_verified_business") != val:
                            matches_all = False
                            break
                    else:
                        # String fields: case-insensitive exact match
                        company_val = str(company.get(key, "")).strip().lower()
                        user_val = str(val).strip().lower()
                        if company_val != user_val:
                            matches_all = False
                            break

                if matches_all:
                    company["_filter_match_ratio"] = 1.0
                    company["_filter_matched_count"] = len(filters_dict)
                    company["_filter_total_count"] = len(filters_dict)
                    filtered_candidates.append(company)

            candidates = filtered_candidates
        else:
            # No filters were actually filled in — use all candidates
            for c in all_candidates:
                c["_filter_match_ratio"] = 1.0
                c["_filter_matched_count"] = 0
                c["_filter_total_count"] = 0
            candidates = all_candidates
    else:
        # No filters object at all — use all candidates
        for c in all_candidates:
            c["_filter_match_ratio"] = 1.0
            c["_filter_matched_count"] = 0
            c["_filter_total_count"] = 0
        candidates = all_candidates

    # If no candidates pass the filters, return early
    if not candidates:
        return []

    # Stage 2: Semantic Vector Similarity Ranking
    # 1. Vectorize the user search query
    query_vector = generate_embedding(search_request.search_query)

    # 2. Compile candidate vectors into a matrix
    candidate_matrix = np.array([
        company["vector_embedding"] for company in candidates
    ])

    # 3. Calculate cosine similarity
    semantic_scores = cosine_similarity([query_vector], candidate_matrix)[0]

    # 4. Attach scores and build clean response objects
    results = []
    for idx, company in enumerate(candidates):
        filter_ratio = company.get("_filter_match_ratio", 1.0)
        matched_count = company.get("_filter_matched_count", 0)
        total_count = company.get("_filter_total_count", 0)
        semantic_score = float(semantic_scores[idx])
        clamped_semantic = max(0.0, min(1.0, semantic_score))
        if total_count > 0:
            combined_score = 0.5 * filter_ratio + 0.5 * clamped_semantic
        else:
            combined_score = clamped_semantic

        # Filter out irrelevant semantic results (semantic similarity threshold >= 0.15)
        if semantic_score < 0.15:
            continue

        res = {
            "id": str(company["_id"]),
            "company_name": company["company_name"],
            "country": company["country"],
            "state_region": company["state_region"],
            "city": company["city"],
            "primary_industry": company["primary_industry"],
            "business_type": company["business_type"],
            "min_order_qty": company["min_order_qty"],
            "company_size": company["company_size"],
            "funding_stage": company["funding_stage"],
            "is_verified_business": company["is_verified_business"],
            "company_bio": company["company_bio"],
            "specialties": company["specialties"],
            "product_service_offerings": company["product_service_offerings"],
            "semantic_score": semantic_score,
            "filter_match_pct": round(filter_ratio * 100),
            "filter_matched": matched_count,
            "filter_total": total_count,
            "combined_score": combined_score,
        }
        results.append(res)

    # Sort by combined score first, then semantic score within any ties
    results.sort(key=lambda x: (x["combined_score"], x["semantic_score"]), reverse=True)

    if search_request.limit is not None and search_request.limit > 0:
        return results[:search_request.limit]

    return results
