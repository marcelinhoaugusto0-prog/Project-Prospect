from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
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
    Fetches business prospects using free OpenStreetMap APIs:
    1. Nominatim for geocoding the location
    2. Overpass API for finding businesses nearby
    100% free, no API key required.
    """
    print(f"Buscando por: {segment} em {location} (Raio: {radius}km)")

    # Step 1: Geocode the location using Nominatim
    lat, lon = geocode_location(location)
    if lat is None or lon is None:
        raise ValueError(f"Não foi possível encontrar a localização: {location}")

    print(f"Coordenadas encontradas: {lat}, {lon}")

    # Step 2: Map the segment to OSM tags
    osm_tags = map_segment_to_osm_tags(segment)
    print(f"Tags OSM: {osm_tags}")

    # Step 3: Query Overpass API for businesses
    radius_meters = radius * 1000  # Convert km to meters
    results = query_overpass(lat, lon, radius_meters, osm_tags, segment)

    # Deduplicate
    unique_results = []
    seen = set()
    for row in results:
        name_lower = row["companyName"].lower().strip()
        if name_lower not in seen and len(name_lower) > 2:
            seen.add(name_lower)
            unique_results.append(row)

    print(f"Busca finalizada. {len(unique_results)} resultados únicos.")
    return unique_results


def geocode_location(location: str):
    """Use Nominatim (free) to geocode a location string to lat/lon."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": location + ", Brasil",
        "format": "json",
        "limit": 1,
        "countrycodes": "br",
    }
    headers = {
        "User-Agent": "ProspectAutomator/1.0 (prospect-app)",
        "Accept-Language": "pt-BR",
    }

    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if not data:
        return None, None

    return float(data[0]["lat"]), float(data[0]["lon"])


def map_segment_to_osm_tags(segment: str):
    """
    Map a business segment search term to OpenStreetMap tags.
    Returns a list of (key, value) tuples for Overpass queries.
    """
    segment_lower = segment.lower().strip()

    # Common mapping of Brazilian business types to OSM tags
    mappings = {
        "clinica": [("amenity", "clinic"), ("amenity", "doctors"), ("healthcare", "clinic")],
        "clínica": [("amenity", "clinic"), ("amenity", "doctors"), ("healthcare", "clinic")],
        "odontolog": [("amenity", "dentist"), ("healthcare", "dentist")],
        "dentista": [("amenity", "dentist"), ("healthcare", "dentist")],
        "restaurante": [("amenity", "restaurant")],
        "lanchonete": [("amenity", "fast_food")],
        "padaria": [("shop", "bakery")],
        "farmacia": [("amenity", "pharmacy"), ("shop", "chemist")],
        "farmácia": [("amenity", "pharmacy"), ("shop", "chemist")],
        "academia": [("leisure", "fitness_centre"), ("amenity", "gym")],
        "pet": [("shop", "pet"), ("amenity", "veterinary")],
        "veterinar": [("amenity", "veterinary")],
        "mercado": [("shop", "supermarket"), ("shop", "convenience")],
        "supermercado": [("shop", "supermarket")],
        "loja": [("shop", "yes")],
        "roupa": [("shop", "clothes")],
        "salao": [("shop", "hairdresser"), ("shop", "beauty")],
        "salão": [("shop", "hairdresser"), ("shop", "beauty")],
        "beleza": [("shop", "beauty"), ("shop", "hairdresser")],
        "barbearia": [("shop", "hairdresser")],
        "escola": [("amenity", "school")],
        "hotel": [("tourism", "hotel")],
        "pousada": [("tourism", "guest_house")],
        "hospital": [("amenity", "hospital")],
        "oficina": [("shop", "car_repair")],
        "mecanica": [("shop", "car_repair")],
        "mecânica": [("shop", "car_repair")],
        "lava": [("shop", "car_wash"), ("amenity", "car_wash")],
        "advogado": [("office", "lawyer")],
        "advocacia": [("office", "lawyer")],
        "contabil": [("office", "accountant")],
        "contábil": [("office", "accountant")],
        "imobiliaria": [("office", "estate_agent")],
        "imobiliária": [("office", "estate_agent")],
        "constru": [("shop", "hardware"), ("shop", "doityourself")],
        "material": [("shop", "hardware"), ("shop", "doityourself")],
        "posto": [("amenity", "fuel")],
        "combustivel": [("amenity", "fuel")],
        "bar": [("amenity", "bar"), ("amenity", "pub")],
        "cafe": [("amenity", "cafe")],
        "café": [("amenity", "cafe")],
        "otica": [("shop", "optician")],
        "ótica": [("shop", "optician")],
        "floricultura": [("shop", "florist")],
        "papelaria": [("shop", "stationery")],
        "livraria": [("shop", "books")],
        "eletro": [("shop", "electronics")],
        "celular": [("shop", "mobile_phone")],
        "informatica": [("shop", "computer")],
        "informática": [("shop", "computer")],
        "joalheria": [("shop", "jewelry")],
        "relojoaria": [("shop", "watches")],
    }

    # Find matching tags
    tags = []
    for keyword, tag_list in mappings.items():
        if keyword in segment_lower:
            tags.extend(tag_list)

    # If no specific mapping found, do a generic search
    if not tags:
        tags = [
            ("shop", ""),      # Any shop
            ("amenity", ""),   # Any amenity
            ("office", ""),    # Any office
        ]

    return tags


def query_overpass(lat: float, lon: float, radius_m: int, tags: list, segment: str):
    """
    Query the Overpass API for businesses matching the given OSM tags
    within the specified radius.
    """
    # Build Overpass QL query
    # We search for nodes and ways with the specified tags
    tag_filters = []
    for key, value in tags:
        if value:
            tag_filters.append(f'node["{key}"="{value}"](around:{radius_m},{lat},{lon});')
            tag_filters.append(f'way["{key}"="{value}"](around:{radius_m},{lat},{lon});')
        else:
            tag_filters.append(f'node["{key}"](around:{radius_m},{lat},{lon});')
            tag_filters.append(f'way["{key}"](around:{radius_m},{lat},{lon});')

    tag_query = "\n    ".join(tag_filters)

    query = f"""
    [out:json][timeout:30];
    (
    {tag_query}
    );
    out body center 100;
    """

    url = "https://overpass-api.de/api/interpreter"
    resp = requests.post(url, data={"data": query}, timeout=45)
    resp.raise_for_status()
    data = resp.json()

    elements = data.get("elements", [])
    print(f"Overpass retornou {len(elements)} elementos.")

    results = []
    for i, el in enumerate(elements):
        tags_data = el.get("tags", {})
        name = tags_data.get("name", "")

        if not name or len(name) < 2:
            continue

        # Filter: if segment has a specific keyword, check the name is relevant
        # (skip entries that clearly don't match)

        phone = (
            tags_data.get("phone", "") or
            tags_data.get("contact:phone", "") or
            tags_data.get("contact:mobile", "")
        )

        # Build address from OSM tags
        addr_parts = []
        street = tags_data.get("addr:street", "")
        number = tags_data.get("addr:housenumber", "")
        city = tags_data.get("addr:city", "")
        suburb = tags_data.get("addr:suburb", "")

        if street:
            addr_parts.append(f"{street}{', ' + number if number else ''}")
        if suburb:
            addr_parts.append(suburb)
        if city:
            addr_parts.append(city)

        address = " - ".join(addr_parts) if addr_parts else ""

        results.append({
            "id": len(results) + 1,
            "companyName": name,
            "phone": phone,
            "address": address,
        })

        if len(results) >= 100:
            break

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
        print("Scraper Error:\n", error_msg)
        return JSONResponse(
            status_code=500,
            content={"detail": str(e), "traceback": error_msg}
        )


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
