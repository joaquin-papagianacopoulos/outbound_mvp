import csv
from pathlib import Path

from sqlalchemy.orm import Session

from app.connectors.serpapi_places import search_places
from app.enrichment import enrich_lead
from app.repository import upsert_lead
from app.schemas import DiscoveryRequest, LeadIn
from app.scoring import apply_ai_score, apply_rule_score


async def discover(db: Session, request: DiscoveryRequest) -> list:
    if request.source != "serpapi":
        return []
    raw_leads = await search_places(request.industry, request.country, request.city, request.limit)
    return [upsert_lead(db, lead) for lead in raw_leads]


async def enrich_and_score(db: Session, lead) -> object:
    lead = await enrich_lead(lead)
    lead = apply_rule_score(lead)
    lead = apply_ai_score(lead)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


async def import_csv(db: Session, path: Path) -> list:
    imported = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            lead = upsert_lead(db, LeadIn(**{k: v for k, v in row.items() if v not in (None, "")}))
            imported.append(await enrich_and_score(db, lead))
    return imported
