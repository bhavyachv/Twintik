# Twintik B2B Matching Algorithm

A high-performance two-stage recommendation and B2B matching engine built with FastAPI and MongoDB (Motor async driver). This application allows B2B buyers to discover, hard-filter, and semantically rank matching suppliers, vendors, and service providers. It features a modern, responsive, glassmorphic web interface to interact with the engine.

---

## Technical Stack & Architecture

- **Backend:** Python 3.9+, FastAPI, Uvicorn, Motor (Async MongoDB client), Pydantic
- **Vector Embeddings:** Sentence-Transformers (`all-MiniLM-L6-v2`) generating 384-dimensional dense vectors
- **Similarity Computation:** NumPy + Scikit-Learn (Cosine Similarity)
- **Frontend:** Vanilla CSS (Tailored dark mode and glassmorphism) + Vanilla JS (Asynchronous API bindings)

### Two-Stage Matching Process

The matching algorithm runs in two distinct, sequential phases:

```
[Raw Company Records in MongoDB]
               |
               v
    +------------------------------------------+
    | STAGE 1: Heuristic Hard-Filtering        |
    | - Executes native indexed MongoDB queries |
    | - Filters: location, industry, MOQ, etc.  |
    | - Reduces dataset size to max 500 records|
    +------------------------------------------+
               |
               v  (Filtered candidate profiles)
    +------------------------------------------+
    | STAGE 2: Semantic Vector Ranking         |
    | - Vectorizes the buyer's query in memory |
    | - Computes cosine similarity scores      |
    | - Sorts matches descending & returns top N|
    +------------------------------------------+
               |
               v
       [Recommended Matches]
```

1. **Stage 1 (Heuristic Filtering):**
   When a B2B search request is received, structural filters (e.g., matching a specific country, industry, or maximum minimum order quantity) are applied directly in MongoDB. Since indexes are created for these fields on startup, this operation executes in milliseconds. Candidate profiles lacking vector embeddings are discarded, and the remaining candidates are limited to 500 elements.
2. **Stage 2 (Semantic Vector Ranking):**
   The buyer's query is encoded in real-time into a 384-dimension float vector using the globally initialized `all-MiniLM-L6-v2` model. The precomputed vector embeddings of the 500 candidate companies are fetched, and Scikit-Learn calculates the cosine similarity. The candidates are then ranked and returned with a similarity percentage.

---

## Setup & Installation

### 1. Prerequisites
- **Python 3.9+** (Tested on Python 3.13)
- **Node.js** (for npx capabilities if running diagnostics)
- **MongoDB** (Local instance or MongoDB Atlas cluster)

### 2. Install Dependencies
Install all package requirements defined in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Database Configuration
Create a `.env` file in the root of the project directory.

#### Local MongoDB Setup:
Ensure MongoDB is running locally on port 27017:
```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=twintik_b2b
```

#### MongoDB Atlas (Cloud) Setup:
```env
MONGODB_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=twintik_b2b
```

---

## Execution Instructions

### 1. Run the FastAPI Application
Launch the dev server using Uvicorn:
```bash
uvicorn app.main:app --reload
```
The server will start at `http://localhost:8000`.

### 2. Populate Sample Seed Data
To initialize the database with 10 sample B2B companies (including 4 UAE-based FinTech companies):
- **Via browser:** Open `http://localhost:8000`, navigate to **System Control**, and click **Seed Database**.
- **Via terminal command:**
  ```bash
  python -m app.seed_data
  ```
- **Via API endpoint:**
  ```bash
  curl -X POST "http://localhost:8000/admin/seed"
  ```

---

## API Examples

### 1. Matchmaker Search Request
Execute a B2B matching query against UAE-based FinTech Series A verified suppliers:
```bash
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{
       "search_query": "looking for scalable payment gateway solutions",
       "filters": {
         "country": "UAE",
         "primary_industry": "FinTech",
         "funding_stage": "Series A",
         "is_verified_business": true
       },
       "limit": 5
     }'
```

### 2. Create a Company Profile
```bash
curl -X POST "http://localhost:8000/companies" \
     -H "Content-Type: application/json" \
     -d '{
       "company_name": "SwiftRemit UAE",
       "country": "UAE",
       "state_region": "Dubai",
       "city": "Dubai",
       "primary_industry": "FinTech",
       "business_type": "SaaS Provider",
       "min_order_qty": 1,
       "company_size": "50-200 employees",
       "funding_stage": "Series A",
       "is_verified_business": true,
       "company_bio": "Global API infrastructure for real-time cross-border remittances and merchant treasury processing.",
       "core_team_designations": "CEO, Head of Remittances, Chief Risk Officer",
       "specialties": "cross-border payments, currency exchange, treasury APIs",
       "product_service_offerings": "payout rails, payment settlement SDK"
     }'
```
*Note: A background task is automatically scheduled to generate vector embeddings for the newly created profile.*

### 3. Update a Company Profile
```bash
curl -X PATCH "http://localhost:8000/companies/<company_id>" \
     -H "Content-Type: application/json" \
     -d '{
       "min_order_qty": 2,
       "company_bio": "Updated bio describing our scalable digital payment infrastructure."
     }'
```

### 4. Paginated Directory Listing
```bash
curl -X GET "http://localhost:8000/companies?page=1&limit=10&country=UAE"
```

### 5. Re-Index Database Vector Embeddings
```bash
curl -X POST "http://localhost:8000/admin/regenerate-embeddings"
```
