from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
import re
import json
import urllib.parse
import traceback

app = FastAPI(title="Prospects API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchParams(BaseModel):
    segment: str
    location: str
    radius: int


def scrape_prospects(segment: str, location: str, radius: int):
    """
    Scrapes business prospects from Google Maps using HTTP requests.
    Works in serverless environments (no browser needed).
    """
    search_query = f"{segment} em {location}"
    print(f"Buscando por: {search_query} (Raio estimado: {radius}km)")

    results = []

    try:
        encoded_query = urllib.parse.quote(search_query)
        url = f"https://www.google.com/maps/search/{encoded_query}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text

        # Extract business data from the HTML
        results = _extract_from_html(html, location)

        if len(results) < 3:
            print("Poucos resultados do HTML. Tentando abordagem alternativa...")
            results = _extract_from_maps_api(search_query, location)

    except Exception as e:
        print(f"Erro durante a raspagem: {e}")
        traceback.print_exc()

    # Deduplicate based on company name
    unique_results = []
    seen = set()
    for row in results:
        name_lower = row["companyName"].lower().strip()
        if name_lower not in seen and len(name_lower) > 2:
            seen.add(name_lower)
            unique_results.append(row)

    print(f"Raspagem finalizada. {len(unique_results)} encontrados.")
    return unique_results


def _extract_from_html(html: str, location: str):
    """Extract business data from Google Maps HTML response."""
    results = []

    aria_labels = re.findall(r'aria-label="([^"]{3,80})"', html)
    phone_numbers = re.findall(r'\(?\d{2}\)?\s*\d{4,5}[-\s]?\d{4}', html)
    addresses = re.findall(
        r'(?:R\.|Rua|Av\.|Avenida|Al\.|Alameda|Pça\.|Praça|Trav\.|Travessa)[^"<]{5,80}',
        html
    )

    data_blocks = re.findall(r'\["0x[0-9a-f]+:[0-9a-f]+","([^"]+)"', html)

    business_names = []
    for name in data_blocks:
        if len(name) > 2 and not name.startswith('http') and not name.startswith('/'):
            business_names.append(name)

    if len(business_names) < 5:
        for label in aria_labels:
            if (len(label) > 3 and
                not label.startswith('http') and
                'Google' not in label and
                'Maps' not in label and
                'Pesquisar' not in label):
                business_names.append(label)

    for i, name in enumerate(business_names[:100]):
        phone = phone_numbers[i] if i < len(phone_numbers) else ""
        address = addresses[i] if i < len(addresses) else location

        results.append({
            "id": i + 1,
            "companyName": name,
            "phone": phone,
            "address": address
        })

    return results


def _extract_from_maps_api(search_query: str, location: str):
    """Alternative extraction using Google Maps search."""
    results = []

    try:
        encoded = urllib.parse.quote(search_query)
        url = f"https://www.google.com/maps/search/{encoded}/"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9",
            "Accept": "text/html,application/xhtml+xml",
            "Referer": "https://www.google.com/",
        }

        session = requests.Session()
        resp = session.get(url, headers=headers, timeout=30, allow_redirects=True)
        text = resp.text

        entries = re.findall(
            r'\\\"([^\\\"]{4,60})\\\"[^}]*?\\\"(\(?\d{2}\)?\s*\d{4,5}[-\s]?\d{4})\\\"',
            text
        )

        for i, (name, phone) in enumerate(entries[:100]):
            results.append({
                "id": i + 1,
                "companyName": name,
                "phone": phone,
                "address": location
            })

        if not results:
            names = re.findall(r'"([^"]{4,60})",null,null,null,null,null,null,null,"[^"]*(?:R\.|Rua|Av\.|Avenida)', text)
            for i, name in enumerate(names[:100]):
                results.append({
                    "id": i + 1,
                    "companyName": name,
                    "phone": "",
                    "address": location
                })

    except Exception as e:
        print(f"Erro na API alternativa: {e}")

    return results


@app.post("/api/prospects")
def generate_prospects(params: SearchParams):
    try:
        results = scrape_prospects(params.segment, params.location, params.radius)
        return {"status": "success", "data": results}
    except Exception as e:
        error_msg = traceback.format_exc()
        print("Scraper Error:\n", error_msg)
        return JSONResponse(status_code=500, content={"detail": str(e), "traceback": error_msg})

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
