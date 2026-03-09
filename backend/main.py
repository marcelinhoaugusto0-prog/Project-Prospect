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

# Google Places API Key - set as environment variable in Vercel
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")


class SearchParams(BaseModel):
    segment: str
    location: str
    radius: int


def scrape_prospects(segment: str, location: str, radius: int):
    """
    Fetches business prospects using Google Places API (Text Search).
    Returns structured business data with name, phone, and address.
    """
    search_query = f"{segment} em {location}"
    print(f"Buscando por: {search_query} (Raio: {radius}km)")

    if not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY não configurada. "
            "Configure a variável de ambiente no Vercel Dashboard."
        )

    results = []

    try:
        # Step 1: Use Text Search to find businesses
        text_search_url = "https://places.googleapis.com/v1/places:searchText"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": (
                "places.displayName,"
                "places.formattedAddress,"
                "places.nationalPhoneNumber,"
                "places.internationalPhoneNumber,"
                "places.websiteUri,"
                "places.id"
            ),
        }

        payload = {
            "textQuery": search_query,
            "languageCode": "pt-BR",
            "maxResultCount": 20,
        }

        # If radius is specified, we can add location bias
        # but for text search, the location is already in the query
        if radius and radius > 0:
            payload["maxResultCount"] = min(20, 20)  # API max is 20 per request

        response = requests.post(text_search_url, json=payload, headers=headers, timeout=30)

        if response.status_code != 200:
            error_detail = response.text
            print(f"Google Places API Error ({response.status_code}): {error_detail}")
            raise Exception(f"Google Places API retornou erro {response.status_code}: {error_detail}")

        data = response.json()
        places = data.get("places", [])

        print(f"Google Places retornou {len(places)} resultados.")

        # If we need more results, paginate
        all_places = list(places)

        # For getting more results, we can make additional requests with page tokens
        # The new API supports pagination via nextPageToken
        # Let's make up to 5 requests to get ~100 results
        page_count = 1
        max_pages = 5  # 5 pages * 20 = up to 100 results

        while page_count < max_pages and len(all_places) < 100:
            # For the new Places API, we use pageToken
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break

            payload["pageToken"] = next_page_token
            response = requests.post(text_search_url, json=payload, headers=headers, timeout=30)

            if response.status_code != 200:
                break

            data = response.json()
            new_places = data.get("places", [])
            if not new_places:
                break

            all_places.extend(new_places)
            page_count += 1
            print(f"Página {page_count}: +{len(new_places)} resultados (total: {len(all_places)})")

        # Step 2: Format results
        for i, place in enumerate(all_places):
            display_name = place.get("displayName", {})
            name = display_name.get("text", "Sem nome") if isinstance(display_name, dict) else str(display_name)

            phone = place.get("nationalPhoneNumber", "") or place.get("internationalPhoneNumber", "")
            address = place.get("formattedAddress", location)

            results.append({
                "id": i + 1,
                "companyName": name,
                "phone": phone,
                "address": address,
            })

    except ValueError:
        raise  # Re-raise API key errors
    except Exception as e:
        print(f"Erro durante a busca: {e}")
        traceback.print_exc()
        raise

    # Deduplicate based on company name
    unique_results = []
    seen = set()
    for row in results:
        name_lower = row["companyName"].lower().strip()
        if name_lower not in seen and len(name_lower) > 2:
            seen.add(name_lower)
            unique_results.append(row)

    print(f"Busca finalizada. {len(unique_results)} resultados únicos encontrados.")
    return unique_results


@app.post("/api/prospects")
def generate_prospects(params: SearchParams):
    try:
        results = scrape_prospects(params.segment, params.location, params.radius)
        return {"status": "success", "data": results}
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})
    except Exception as e:
        error_msg = traceback.format_exc()
        print("Scraper Error:\n", error_msg)
        return JSONResponse(status_code=500, content={"detail": str(e), "traceback": error_msg})


@app.get("/api/health")
def health_check():
    return {"status": "ok", "api_key_configured": bool(GOOGLE_API_KEY)}
