import httpx

from app.config import get_settings
from app.schemas import LeadIn


async def search_places(industry: str, country: str, city: str, limit: int = 20) -> list[LeadIn]:
    settings = get_settings()
    if not settings.serpapi_key:
        return []

    params = {
        "engine": "google_maps",
        "q": f"{industry} {city} {country}",
        "type": "search",
        "api_key": settings.serpapi_key,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get("https://serpapi.com/search.json", params=params)
        response.raise_for_status()
        data = response.json()

    leads = []
    for item in data.get("local_results", [])[:limit]:
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
    return leads
