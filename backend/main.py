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

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")


class SearchParams(BaseModel):
    segment: str
    location: str
    radius: int


def scrape_prospects(segment: str, location: str, radius: int):
    """
    Fetches business prospects using Google Places API (New) - Text Search.
    Free tier: $200/month credit from Google (covers ~6000+ searches/month).
    """
    search_query = f"{segment} em {location}"
    print(f"Buscando por: {search_query} (Raio: {radius}km)")

    if not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY não configurada. "
            "Acesse o Vercel Dashboard > Settings > Environment Variables "
            "e adicione sua chave da Google Places API."
        )

    all_results = []

    try:
        # --- Google Places API (New) - Text Search ---
        url = "https://places.googleapis.com/v1/places:searchText"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": ",".join([
                "places.displayName",
                "places.formattedAddress",
                "places.nationalPhoneNumber",
                "places.internationalPhoneNumber",
                "places.websiteUri",
                "places.id",
                "nextPageToken",
            ]),
        }

        payload = {
            "textQuery": search_query,
            "languageCode": "pt-BR",
            "maxResultCount": 20,
        }

        # First request
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            error_text = resp.text
            print(f"Places API error ({resp.status_code}): {error_text}")
            raise Exception(f"Google Places API erro {resp.status_code}: {error_text}")

        data = resp.json()
        places = data.get("places", [])
        all_results.extend(places)
        print(f"Página 1: {len(places)} resultados")

        # Paginate to get more results (up to 5 pages = ~100 results)
        page = 1
        while page < 5 and len(all_results) < 100:
            next_token = data.get("nextPageToken")
            if not next_token:
                break

            page += 1
            payload["pageToken"] = next_token
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            if resp.status_code != 200:
                break

            data = resp.json()
            new_places = data.get("places", [])
            if not new_places:
                break

            all_results.extend(new_places)
            print(f"Página {page}: +{len(new_places)} resultados (total: {len(all_results)})")

    except ValueError:
        raise
    except Exception as e:
        print(f"Erro na busca: {e}")
        traceback.print_exc()
        raise

    # Format results
    formatted = []
    seen = set()
    for i, place in enumerate(all_results):
        display_name = place.get("displayName", {})
        name = display_name.get("text", "") if isinstance(display_name, dict) else str(display_name)

        if not name or len(name) < 2:
            continue

        name_lower = name.lower().strip()
        if name_lower in seen:
            continue
        seen.add(name_lower)

        phone = place.get("nationalPhoneNumber", "") or place.get("internationalPhoneNumber", "")
        address = place.get("formattedAddress", "")

        formatted.append({
            "id": len(formatted) + 1,
            "companyName": name,
            "phone": phone,
            "address": address,
        })

    print(f"Busca finalizada. {len(formatted)} resultados únicos.")
    return formatted


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
    return {"status": "ok", "api_key_configured": bool(GOOGLE_API_KEY)}
