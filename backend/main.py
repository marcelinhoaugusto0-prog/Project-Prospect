from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
import traceback
import time
import re

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


# =========================================================================
# SEGMENT -> OSM TAGS
# =========================================================================
SEGMENT_TAGS = {
    "clinica": [("amenity", "clinic"), ("amenity", "doctors"), ("healthcare", "clinic")],
    "clínica": [("amenity", "clinic"), ("amenity", "doctors"), ("healthcare", "clinic")],
    "odonto": [("amenity", "dentist"), ("healthcare", "dentist")],
    "dentista": [("amenity", "dentist")],
    "hospital": [("amenity", "hospital")],
    "farmacia": [("amenity", "pharmacy")],
    "farmácia": [("amenity", "pharmacy")],
    "veterinar": [("amenity", "veterinary")],
    "laboratorio": [("healthcare", "laboratory")],
    "laboratório": [("healthcare", "laboratory")],
    "otica": [("shop", "optician")],
    "ótica": [("shop", "optician")],
    "restaurante": [("amenity", "restaurant")],
    "lanchonete": [("amenity", "fast_food")],
    "padaria": [("shop", "bakery")],
    "pizzaria": [("amenity", "restaurant")],
    "hamburgueria": [("amenity", "fast_food")],
    "sorveteria": [("amenity", "ice_cream")],
    "bar": [("amenity", "bar"), ("amenity", "pub")],
    "cafe": [("amenity", "cafe")],
    "café": [("amenity", "cafe")],
    "confeitaria": [("shop", "confectionery")],
    "doceria": [("shop", "confectionery")],
    "salao": [("shop", "hairdresser"), ("shop", "beauty")],
    "salão": [("shop", "hairdresser"), ("shop", "beauty")],
    "barbearia": [("shop", "hairdresser")],
    "beleza": [("shop", "beauty")],
    "estetica": [("shop", "beauty")],
    "estética": [("shop", "beauty")],
    "academia": [("leisure", "fitness_centre")],
    "mercado": [("shop", "supermarket"), ("shop", "convenience")],
    "supermercado": [("shop", "supermarket")],
    "loja": [("shop", "yes")],
    "roupa": [("shop", "clothes")],
    "pet": [("shop", "pet")],
    "floricultura": [("shop", "florist")],
    "papelaria": [("shop", "stationery")],
    "livraria": [("shop", "books")],
    "eletro": [("shop", "electronics")],
    "celular": [("shop", "mobile_phone")],
    "informatica": [("shop", "computer")],
    "informática": [("shop", "computer")],
    "moveis": [("shop", "furniture")],
    "móveis": [("shop", "furniture")],
    "constru": [("shop", "hardware"), ("shop", "doityourself")],
    "material": [("shop", "hardware")],
    "advogado": [("office", "lawyer")],
    "advocacia": [("office", "lawyer")],
    "contabil": [("office", "accountant")],
    "contábil": [("office", "accountant")],
    "imobiliaria": [("office", "estate_agent")],
    "imobiliária": [("office", "estate_agent")],
    "escola": [("amenity", "school")],
    "creche": [("amenity", "kindergarten")],
    "autoescola": [("amenity", "driving_school")],
    "oficina": [("shop", "car_repair")],
    "mecanica": [("shop", "car_repair")],
    "mecânica": [("shop", "car_repair")],
    "lava": [("amenity", "car_wash")],
    "posto": [("amenity", "fuel")],
    "pneu": [("shop", "tyres")],
    "hotel": [("tourism", "hotel")],
    "pousada": [("tourism", "guest_house")],
    "joalheria": [("shop", "jewelry")],
    "perfumaria": [("shop", "perfumery")],
}


def get_tags(segment: str):
    s = segment.lower().strip()
    tags = []
    for kw, tl in SEGMENT_TAGS.items():
        if kw in s:
            tags.extend(tl)
    return list(set(tags))


def geocode(location: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": f"{location}, Brasil", "format": "json", "limit": 1, "countrycodes": "br"}
    headers = {"User-Agent": "ProspectApp/2.0", "Accept-Language": "pt-BR"}
    r = requests.get(url, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    d = r.json()
    if not d:
        return None, None
    return float(d[0]["lat"]), float(d[0]["lon"])


def overpass_by_tags(lat, lon, radius_m, tags):
    """Search Overpass by OSM tags (primary strategy)."""
    filters = []
    for key, val in tags:
        for t in ["node", "way", "relation"]:
            filters.append(f'{t}["{key}"="{val}"]["name"](around:{radius_m},{lat},{lon});')

    query = f"""[out:json][timeout:60];({chr(10).join(filters)});out body center 100;"""
    r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=90)
    r.raise_for_status()
    return r.json().get("elements", [])


def overpass_by_name(lat, lon, radius_m, segment):
    """Search Overpass by name regex (catches everything the tag search misses)."""
    # Escape special regex chars in segment
    safe_seg = re.sub(r'[^a-zA-ZÀ-ÿ0-9 ]', '', segment)
    query = f"""[out:json][timeout:60];
    (
    node["name"~"{safe_seg}",i](around:{radius_m},{lat},{lon});
    way["name"~"{safe_seg}",i](around:{radius_m},{lat},{lon});
    );
    out body center 100;"""
    r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=90)
    r.raise_for_status()
    return r.json().get("elements", [])


def nominatim_search(segment, location):
    """Secondary source: Nominatim free text search."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": f"{segment} {location} Brasil",
        "format": "json", "limit": 50,
        "countrycodes": "br", "addressdetails": 1,
    }
    headers = {"User-Agent": "ProspectApp/2.0", "Accept-Language": "pt-BR"}
    r = requests.get(url, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()


def format_element(el):
    """Format an Overpass element into a result dict."""
    tags = el.get("tags", {})
    name = tags.get("name", "")
    if not name or len(name) < 2:
        return None

    phone = tags.get("phone", "") or tags.get("contact:phone", "") or tags.get("contact:mobile", "")
    website = tags.get("website", "") or tags.get("contact:website", "")

    parts = []
    street = tags.get("addr:street", "")
    number = tags.get("addr:housenumber", "")
    suburb = tags.get("addr:suburb", "")
    city = tags.get("addr:city", "")
    if street:
        parts.append(f"{street}{', ' + number if number else ''}")
    if suburb:
        parts.append(suburb)
    if city:
        parts.append(city)

    return {
        "companyName": name,
        "phone": phone,
        "address": " - ".join(parts) if parts else "",
        "website": website,
        "category": tags.get("amenity", "") or tags.get("shop", "") or tags.get("office", "") or tags.get("leisure", "") or "",
    }


def format_nominatim(items):
    results = []
    for item in items:
        name = item.get("display_name", "").split(",")[0]
        if not name or len(name) < 3:
            continue
        addr = item.get("address", {})
        parts = []
        road = addr.get("road", "")
        num = addr.get("house_number", "")
        sub = addr.get("suburb", "") or addr.get("neighbourhood", "")
        city = addr.get("city", "") or addr.get("town", "") or addr.get("village", "")
        if road:
            parts.append(f"{road}{', ' + num if num else ''}")
        if sub:
            parts.append(sub)
        if city:
            parts.append(city)
        results.append({
            "companyName": name,
            "phone": "",
            "address": " - ".join(parts) if parts else "",
            "website": "",
            "category": "",
        })
    return results


def scrape_prospects(segment: str, location: str, radius: int):
    print(f"Buscando: {segment} em {location} (Raio: {radius}km)")

    lat, lon = geocode(location)
    if lat is None:
        raise ValueError(f"Localização não encontrada: {location}")
    print(f"Coords: {lat}, {lon}")

    tags = get_tags(segment)
    radius_m = radius * 1000
    all_results = []

    # Strategy 1: Overpass by OSM tags
    if tags:
        try:
            print(f"[1] Overpass por tags ({len(tags)} tags)...")
            elements = overpass_by_tags(lat, lon, radius_m, tags)
            print(f"    -> {len(elements)} elementos")
            for el in elements:
                r = format_element(el)
                if r:
                    all_results.append(r)
        except Exception as e:
            print(f"    Erro: {e}")

    # Strategy 2: Overpass by name (catches businesses not properly tagged)
    try:
        print(f"[2] Overpass por nome '{segment}'...")
        elements = overpass_by_name(lat, lon, radius_m, segment)
        print(f"    -> {len(elements)} elementos")
        for el in elements:
            r = format_element(el)
            if r:
                all_results.append(r)
    except Exception as e:
        print(f"    Erro: {e}")

    # Strategy 3: Nominatim free text search (extra results)
    if len(all_results) < 80:
        try:
            time.sleep(1)
            print("[3] Nominatim busca textual...")
            items = nominatim_search(segment, location)
            print(f"    -> {len(items)} itens")
            all_results.extend(format_nominatim(items))
        except Exception as e:
            print(f"    Erro: {e}")

    # Deduplicate
    unique = []
    seen = set()
    for row in all_results:
        key = row["companyName"].lower().strip()
        if key not in seen and len(key) > 2:
            seen.add(key)
            row["id"] = len(unique) + 1
            unique.append(row)

    print(f"Total final: {len(unique)} resultados únicos")
    return unique[:100]


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
    return {"status": "ok"}
