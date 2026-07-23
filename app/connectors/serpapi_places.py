import httpx

from app.config import get_settings
from app.schemas import LeadIn


RESULTS_PER_PAGE = 20
MAX_GOOGLE_MAPS_OFFSET = 100


def estimate_serpapi_credits(limit: int) -> int:
    if limit <= 0:
        return 0
    pages = (limit + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    return min(pages, (MAX_GOOGLE_MAPS_OFFSET // RESULTS_PER_PAGE) + 1)


async def search_places(industry: str, country: str, city: str, limit: int = 20) -> list[LeadIn]:
    settings = get_settings()
    if not settings.serpapi_key:
        return []

    leads = []
    seen = set()
    requested = max(1, min(limit, 120))
    async with httpx.AsyncClient(timeout=30) as client:
        for start in range(0, min(requested, MAX_GOOGLE_MAPS_OFFSET + RESULTS_PER_PAGE), RESULTS_PER_PAGE):
            params = {
                "engine": "google_maps",
                "q": f"{industry} {city} {country}",
                "type": "search",
                "start": start,
                "api_key": settings.serpapi_key,
            }
            response = await client.get("https://serpapi.com/search.json", params=params)
            response.raise_for_status()
            data = response.json()
            results = data.get("local_results", [])
            if not results:
                break

            for item in results:
                key = item.get("place_id") or item.get("data_id") or item.get("title")
                if key in seen:
                    continue
                seen.add(key)
                leads.append(
                    LeadIn(
                        business_name=item.get("title") or "Sin nombre",
                        industry=industry,
                        country=country,
                        city=city,
                        source="google_maps_serpapi",
                        source_url=item.get("place_id_search") or item.get("link"),
                        website=item.get("website"),
                        phone=item.get("phone"),
                        address=item.get("address"),
                    )
                )
                if len(leads) >= requested:
                    return leads

            if "serpapi_pagination" not in data:
                break
    return leads
