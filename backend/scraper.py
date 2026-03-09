import requests
import re
import json
import urllib.parse

def scrape_prospects(segment: str, location: str, radius: int):
    """
    Scrapes business prospects from Google Maps using HTTP requests.
    Works in serverless environments (no browser needed).
    """
    search_query = f"{segment} em {location}"
    print(f"Buscando por: {search_query} (Raio estimado: {radius}km)")

    results = []

    try:
        # Use Google Maps search URL and parse the embedded JSON data
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

        # Google Maps embeds data in JavaScript. We parse the page for business listings.
        # Look for the pattern that contains business data in the page source.
        
        # Method 1: Parse from embedded JS data
        # Google Maps stores data in window.APP_INITIALIZATION_STATE or similar
        results = _extract_from_html(html, location)

        # If Method 1 didn't find enough results, try the Places API approach
        if len(results) < 3:
            print("Poucos resultados do HTML. Tentando abordagem alternativa...")
            results = _extract_from_maps_api(search_query, location)

    except Exception as e:
        print(f"Erro durante a raspagem: {e}")
        import traceback
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

    # Google Maps embeds structured data in the page as JSON arrays
    # Pattern: look for arrays containing business info
    # The data is typically in a large JS variable
    
    # Try to find business names and phone numbers from the raw HTML
    # Google Maps returns data in a specific format in script tags

    # Look for structured data patterns
    # Pattern for business listings in Google Maps HTML
    name_pattern = re.findall(
        r'\[\"([^"]{3,60})\"\s*,\s*\"[^"]*\"\s*,\s*\[[\d.]+,\s*[\d.-]+\]',
        html
    )

    # Alternative: find all potential business names from aria-labels
    aria_labels = re.findall(r'aria-label="([^"]{3,80})"', html)

    # Find phone numbers in the HTML
    phone_numbers = re.findall(
        r'\(?\d{2}\)?\s*\d{4,5}[-\s]?\d{4}',
        html
    )

    # Find addresses
    addresses = re.findall(
        r'(?:R\.|Rua|Av\.|Avenida|Al\.|Alameda|Pça\.|Praça|Trav\.|Travessa)[^"<]{5,80}',
        html
    )

    # Try to extract from the large data blob that Google Maps uses
    # Look for patterns like: [null,"Business Name",null,...,"(11) 1234-5678",...,"Address"]
    data_blocks = re.findall(r'\["0x[0-9a-f]+:[0-9a-f]+","([^"]+)"', html)

    # Combine all found business names
    business_names = []
    
    # From data blocks (most reliable)
    for name in data_blocks:
        if len(name) > 2 and not name.startswith('http') and not name.startswith('/'):
            business_names.append(name)

    # From aria labels as fallback
    if len(business_names) < 5:
        for label in aria_labels:
            if (len(label) > 3 and 
                not label.startswith('http') and 
                'Google' not in label and
                'Maps' not in label and
                'Pesquisar' not in label):
                business_names.append(label)

    # Build results
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
    """
    Alternative extraction using Google Maps internal API endpoint.
    This sends a request similar to what the Maps frontend does.
    """
    results = []

    try:
        # Google Maps uses an internal API for search results
        # We can query it directly
        encoded = urllib.parse.quote(search_query)
        
        # Use the textsearch endpoint that Google Maps frontend uses
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

        # Parse the response for business data
        # Google Maps returns data in a specific protobuf-like JSON format
        # embedded in the HTML page

        # Extract all potential business entries
        # Pattern: businesses are in arrays with coordinates and details
        
        # Find business info blocks - they typically contain name, rating, address, phone
        # The pattern varies but usually has the format:
        # [null, null, null, [null, "Business Name"], ...]
        
        # Simple regex to find business-like entries
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

        # If regex didn't work, try another pattern
        if not results:
            # Look for unescaped business data
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


if __name__ == "__main__":
    # Test script execution
    res = scrape_prospects("clinicas odontologicas", "São Paulo", 5)
    for r in res:
        print(r["companyName"], "-", r["phone"])
