from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CompanyBase(BaseModel):
    company_name: str = Field(..., description="Name of the B2B company")
    country: str = Field(..., description="Country of operation")
    state_region: str = Field(..., description="State or region")
    city: str = Field(..., description="City of location")
    primary_industry: str = Field(..., description="Primary industry sector")
    business_type: str = Field(..., description="Business model / category")
    min_order_qty: int = Field(..., description="Minimum order quantity (MOQ)", ge=0)
    company_size: str = Field(..., description="Range of employee count")
    funding_stage: str = Field(..., description="Current funding round")
    is_verified_business: bool = Field(..., description="Verification status")
    company_bio: str = Field(..., description="Text details about the company")
    core_team_designations: str = Field(..., description="Roles of key team members")
    specialties: str = Field(..., description="Keywords of core competencies")
    product_service_offerings: str = Field(..., description="Products and services description")

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    country: Optional[str] = None
    state_region: Optional[str] = None
    city: Optional[str] = None
    primary_industry: Optional[str] = None
    business_type: Optional[str] = None
    min_order_qty: Optional[int] = Field(None, ge=0)
    company_size: Optional[str] = None
    funding_stage: Optional[str] = None
    is_verified_business: Optional[bool] = None
    company_bio: Optional[str] = None
    core_team_designations: Optional[str] = None
    specialties: Optional[str] = None
    product_service_offerings: Optional[str] = None

class CompanyResponse(CompanyBase):
    id: str = Field(..., description="Hex string representation of MongoDB ObjectId")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class SearchFilters(BaseModel):
    country: Optional[str] = None
    state_region: Optional[str] = None
    city: Optional[str] = None
    primary_industry: Optional[str] = None
    business_type: Optional[str] = None
    min_order_qty: Optional[int] = Field(None, ge=0)
    company_size: Optional[str] = None
    funding_stage: Optional[str] = None
    is_verified_business: Optional[bool] = None

class SearchRequest(BaseModel):
    search_query: str = Field(..., description="Buyer's query (e.g., product or service requirements)")
    filters: Optional[SearchFilters] = None
    limit: Optional[int] = Field(default=None, description="Maximum number of recommendations to return")

class SearchResult(BaseModel):
    id: str
    company_name: str
    country: str
    state_region: str
    city: str
    primary_industry: str
    business_type: str
    min_order_qty: int
    company_size: str
    funding_stage: str
    is_verified_business: bool
    company_bio: str
    specialties: str
    product_service_offerings: str
    semantic_score: float = Field(..., description="Cosine similarity ranking score")
    filter_match_pct: int = Field(..., description="Percentage of matching filters")
    filter_matched: int = Field(..., description="Number of filters matched")
    filter_total: int = Field(..., description="Total filters applied")
    combined_score: float = Field(..., description="Combined hard filter and semantic vector matching score")

    class Config:
        from_attributes = True
