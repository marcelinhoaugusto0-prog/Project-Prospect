from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
import os
import traceback

app = FastAPI(title="Prospects API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Outscraper API Key - free tier: 500 records, no credit card needed
# Get yours at: https://outscraper.com (sign up -> API -> copy key)
OUTSCRAPER_API_KEY = os.environ.get("OUTSCRAPER_API_KEY", "")


class SearchParams(BaseModel):
    segment: str
    location: str
    radius: int


def scrape_prospects(segment: str, location: str, radius: int):
    """
    Fetches business prospects using Outscraper Google Maps API.
    Free tier: 500 records (no credit card required).
    Returns rich data: name, phone, address, website, rating, reviews.
    """
    query = f"{segment}, {location}, Brasil"
    print(f"Buscando via Outscraper: {query}")

    if not OUTSCRAPER_API_KEY:
        raise ValueError(
            "OUTSCRAPER_API_KEY não configurada. "
            "Crie uma conta gratuita em https://outscraper.com, "
            "copie sua API key e adicione como variável de ambiente no Vercel."
        )

    url = "https://api.outscraper.cloud/google-maps-search"
    params = {
        "query": query,
        "limit": min(100, 100),
        "async": "false",
        "language": "pt",
        "region": "BR",
    }
    headers = {
        "X-API-KEY": OUTSCRAPER_API_KEY,
    }

    resp = requests.get(url, params=params, headers=headers, timeout=120)

    if resp.status_code == 401:
        raise ValueError("API key inválida. Verifique sua OUTSCRAPER_API_KEY.")
    if resp.status_code == 402:
        raise ValueError("Créditos gratuitos esgotados na Outscraper.")
    if resp.status_code != 200:
        raise Exception(f"Outscraper API erro {resp.status_code}: {resp.text}")

    data = resp.json()

    if data.get("status") != "Success":
        raise Exception(f"Outscraper retornou status: {data.get('status')}")

    # The API returns data as nested arrays: data -> [batch] -> [places]
    raw_places = []
    for batch in data.get("data", []):
        if isinstance(batch, list):
            raw_places.extend(batch)
        elif isinstance(batch, dict):
            raw_places.append(batch)

    print(f"Outscraper retornou {len(raw_places)} resultados.")

    # Format results
    results = []
    seen = set()
    for place in raw_places:
        name = place.get("name", "")
        if not name or len(name) < 2:
            continue

        name_lower = name.lower().strip()
        if name_lower in seen:
            continue
        seen.add(name_lower)

        phone = place.get("phone", "") or ""
        address = place.get("address", "") or place.get("full_address", "") or ""
        website = place.get("website", "") or ""
        rating = place.get("rating", None)
        reviews = place.get("reviews", 0) or 0
        category = place.get("type", "") or place.get("category", "") or ""
        city = place.get("city", "") or ""

        results.append({
            "id": len(results) + 1,
            "companyName": name,
            "phone": phone,
            "address": address,
            "website": website,
            "rating": rating,
            "reviews": reviews,
            "category": category,
            "city": city,
        })

    print(f"Total: {len(results)} resultados únicos formatados.")
    return results


@app.post("/api/prospects")
def generate_prospects(params: SearchParams):
    try:
        results = scrape_prospects(params.segment, params.location, params.radius)
        return {"status": "success", "data": results}
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    except Exception as e:
        error_msg = traceback.format_exc()
        print("Error:\n", error_msg)
        return JSONResponse(status_code=500, content={"detail": str(e)})


@app.get("/api/health")
def health_check():
    return {"status": "ok", "api_key_configured": bool(OUTSCRAPER_API_KEY)}
