import time
from playwright.sync_api import sync_playwright
import re

def scrape_prospects(segment: str, location: str, radius: int):
    # This function uses Playwright to scrape business info from Google Maps.
    search_query = f"{segment} em {location}"
    print(f"Buscando por: {search_query} (Raio estimado: {radius}km)")
    
    results = []
    
    with sync_playwright() as p:
        # Launch headless browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="pt-BR"
        )
        page = context.new_page()
        
        try:
            # Navigate directly to Google Maps Search
            url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
            page.goto(url, timeout=60000)
            
            # Diagnostic saves
            page.screenshot(path="debug_maps.png")
            html = page.content()
            with open("debug_maps.html", "w", encoding="utf-8") as f:
                f.write(html)
            
            # Wait for the results feed container
            try:
                page.wait_for_selector('div[role="feed"]', timeout=15000)
            except Exception:
                print("Could not find the results feed. Maps layout might have changed or no results.")
                browser.close()
                return []
            
            # Scroll to load more results (simulate scrolling the sidebar)
            feed_element = page.query_selector('div[role="feed"]')
            
            if feed_element:
                print("Carregando resultados...")
                for _ in range(15):  # Scroll 15 times to get around 100+ results
                    feed_element.evaluate("el => el.scrollTop = el.scrollHeight")
                    time.sleep(1.5)
            
            # Extract elements from the list
            # We look for the main containers holding business information
            items = page.query_selector_all('div.fontBodyMedium')
            
            print(f"Encontrados {len(items)} blocos. Extraindo informações...")
            
            for item in items:
                if len(results) >= 100:
                    break
                    
                text_content = item.inner_text()
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                
                if not lines or len(lines) < 2:
                    continue
                    
                # Normally the first line in this specific div is the company name
                company_name = lines[0]
                
                # Skip if it looks like an ad or irrelevant small text
                if len(company_name) < 3 or "Anúncio" in company_name:
                    continue
                
                # Simple extraction heuristics based on Maps formatting
                # Look for Brazilian phone numbers
                phone_match = re.search(r'(\(?\d{2}\)?\s*)?\d{4,5}[-\s]?\d{4}', text_content)
                phone = phone_match.group(0) if phone_match else ""
                
                # For address, look for clues or pick a line not containing ranking stars
                address = location
                for line in lines[1:]:
                    if any(char.isdigit() for char in line) and "m" in line.lower() and not "avali" in line.lower() and "." not in line:
                        address += " - " + line
                        break
                        
                # Provide simulated "Website Extraction" fallback since true email extraction 
                # takes too long per-company for a real-time dashboard endpoint
                results.append({
                    "id": len(results) + 1,
                    "companyName": company_name,
                    "phone": phone,
                    "address": address
                })
                
        except Exception as e:
            print(f"Erro durante a raspagem: {e}")
            
        finally:
            browser.close()
            
    # Deduplicate based on company name
    unique_results = []
    seen = set()
    for row in results:
        if row["companyName"] not in seen:
            seen.add(row["companyName"])
            unique_results.append(row)
            
    print(f"Raspagem finalizada. {len(unique_results)} encontrados.")
    return unique_results

if __name__ == "__main__":
    # Test script execution
    res = scrape_prospects("clinicas odontologicas", "São Paulo", 5)
    for r in res:
        print(r["companyName"], "-", r["phone"])
