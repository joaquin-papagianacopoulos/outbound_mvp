from pathlib import Path
from datetime import datetime
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.channels.chatwoot import send_whatsapp_template_via_chatwoot
from app.connectors.serpapi_places import estimate_serpapi_credits, search_places
from app.db import get_db, init_db
from app.models import ContactEvent, Lead
from app.outreach_limits import check_whatsapp_send_limits
from app.personalization import ai_message
from app.pipeline import discover, enrich_and_score
from app.repository import find_existing_lead, lead_matches_filters, list_leads, stats, upsert_lead
from app.schemas import DiscoveryRequest, LeadIn

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app = FastAPI(title="ENVI Outbound MVP")


def build_lead_filters(
    has_web: bool = False,
    has_email: bool = False,
    has_phone: bool = False,
    has_whatsapp: bool = False,
    has_instagram: bool = False,
    has_ecommerce: bool = False,
    has_multibranch: bool = False,
    priority: str = "",
    city: str = "",
    industry: str = "",
) -> dict:
    return {
        "has_web": has_web,
        "has_email": has_email,
        "has_phone": has_phone,
        "has_whatsapp": has_whatsapp,
        "has_instagram": has_instagram,
        "has_ecommerce": has_ecommerce,
        "has_multibranch": has_multibranch,
        "priority": priority if priority in {"A", "B", "C"} else "",
        "city": city.strip(),
        "industry": industry.strip(),
    }


def filters_to_query(filters: dict) -> dict:
    query = {}
    for key, value in filters.items():
        if isinstance(value, bool):
            if value:
                query[key] = "true"
        elif value:
            query[key] = value
    return query


def create_draft_for_lead(db: Session, lead: Lead, channel: str, step: str) -> ContactEvent:
    subject, body = ai_message(lead, channel, step)
    event = ContactEvent(lead_id=lead.id, channel=channel, step=step, subject=subject, body=body, status="draft")
    db.add(event)
    lead.status = "drafted"
    return event


def serialize_event(event: ContactEvent, lead: Lead | None = None) -> dict:
    return {
        "event_id": event.id,
        "lead_id": event.lead_id,
        "lead_name": lead.business_name if lead else None,
        "channel": event.channel,
        "step": event.step,
        "subject": event.subject,
        "body": event.body,
        "status": event.status,
    }


def apply_send_result(db: Session, lead: Lead, event: ContactEvent, status: str) -> None:
    event.status = status
    if status in {"sent", "dry_run"}:
        lead.status = "contacted" if status == "sent" else "drafted"
        if status == "sent":
            lead.last_contacted_at = datetime.utcnow()
    elif status in {"failed", "config_error"}:
        lead.status = "delivery_failed"
    db.commit()


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    page: str = "leads",
    screen: str = "",
    view: str = "all",
    has_web: bool = False,
    has_email: bool = False,
    has_phone: bool = False,
    has_whatsapp: bool = False,
    has_instagram: bool = False,
    has_ecommerce: bool = False,
    has_multibranch: bool = False,
    priority: str = "",
    city: str = "",
    industry: str = "",
    db: Session = Depends(get_db),
):
    if screen in {"discover", "leads"} and page == "leads":
        page = screen
    current_screen = page if page in {"discover", "leads", "campaign"} else "leads"
    if current_screen == "campaign" and not any(
        [has_web, has_email, has_phone, has_whatsapp, has_instagram, has_ecommerce, has_multibranch, priority, city, industry]
    ):
        has_whatsapp = True
        priority = "A"
    view_to_status = {
        "new": "new",
        "drafted": "drafted",
        "contacted": "contacted",
        "replied": "replied",
        "not_interested": "not_interested",
        "not_fit": "not_fit",
    }
    status_filter = view_to_status.get(view)
    lead_filters = build_lead_filters(
        has_web=has_web,
        has_email=has_email,
        has_phone=has_phone,
        has_whatsapp=has_whatsapp,
        has_instagram=has_instagram,
        has_ecommerce=has_ecommerce,
        has_multibranch=has_multibranch,
        priority=priority,
        city=city,
        industry=industry,
    )
    leads = list_leads(db, limit=200, status=status_filter, filters=lead_filters)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "leads": leads,
            "stats": stats(db),
            "current_screen": current_screen,
            "current_view": view,
            "lead_filters": lead_filters,
            "estimated_serpapi_credits": estimate_serpapi_credits(20),
        },
    )


@app.post("/api/leads")
async def create_lead(lead: LeadIn, db: Session = Depends(get_db)):
    saved = upsert_lead(db, lead)
    saved = await enrich_and_score(db, saved)
    return {"id": saved.id, "fit_score": saved.fit_score, "priority": saved.priority}


@app.post("/api/discover")
async def api_discover(request: DiscoveryRequest, db: Session = Depends(get_db)):
    found = await discover(db, request)
    scored = [await enrich_and_score(db, lead) for lead in found]
    return {"found": len(scored), "lead_ids": [lead.id for lead in scored]}


@app.post("/discover")
async def form_discover(
    industry: str = Form(...),
    country: str = Form("Argentina"),
    city: str = Form(...),
    limit: int = Form(20),
    has_web: bool = Form(False),
    has_email: bool = Form(False),
    has_phone: bool = Form(False),
    has_whatsapp: bool = Form(False),
    has_instagram: bool = Form(False),
    has_ecommerce: bool = Form(False),
    has_multibranch: bool = Form(False),
    priority: str = Form(""),
    db: Session = Depends(get_db),
):
    lead_filters = build_lead_filters(
        has_web=has_web,
        has_email=has_email,
        has_phone=has_phone,
        has_whatsapp=has_whatsapp,
        has_instagram=has_instagram,
        has_ecommerce=has_ecommerce,
        has_multibranch=has_multibranch,
        priority=priority,
        city=city,
        industry=industry,
    )
    raw_leads = await search_places(industry, country, city, limit)
    scored = []
    matched = []
    saved = []
    for raw_lead in raw_leads:
        existed = find_existing_lead(db, raw_lead)
        lead = upsert_lead(db, raw_lead)
        lead = await enrich_and_score(db, lead)
        scored.append(lead)
        if lead_matches_filters(lead, lead_filters):
            matched.append(lead)
            saved.append(lead)
            continue
        if existed is None:
            db.execute(delete(ContactEvent).where(ContactEvent.lead_id == lead.id))
            db.delete(lead)
            db.commit()

    credits = estimate_serpapi_credits(limit)
    query = {
        "page": "leads",
        "view": "all",
        **filters_to_query(lead_filters),
        "last_found": str(len(scored)),
        "last_matched": str(len(matched)),
        "last_saved": str(len(saved)),
        "last_credits": str(credits),
    }
    return RedirectResponse("/?" + urlencode(query), status_code=303)


@app.post("/api/leads/{lead_id}/enrich")
async def api_enrich(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead = await enrich_and_score(db, lead)
    return {"id": lead.id, "fit_score": lead.fit_score, "priority": lead.priority}


@app.post("/api/leads/delete-bulk")
def bulk_delete_leads(lead_ids: str = Form(...), db: Session = Depends(get_db)):
    ids = []
    for raw_id in lead_ids.split(","):
        raw_id = raw_id.strip()
        if raw_id:
            try:
                ids.append(int(raw_id))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid lead id: {raw_id}") from None
    if not ids:
        raise HTTPException(status_code=400, detail="No leads selected")
    db.execute(delete(ContactEvent).where(ContactEvent.lead_id.in_(ids)))
    result = db.execute(delete(Lead).where(Lead.id.in_(ids)))
    db.commit()
    return {"deleted": result.rowcount or 0}


def parse_lead_ids(lead_ids: str) -> list[int]:
    ids = []
    for raw_id in lead_ids.split(","):
        raw_id = raw_id.strip()
        if raw_id:
            try:
                ids.append(int(raw_id))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid lead id: {raw_id}") from None
    return ids


@app.post("/api/leads/status-bulk")
def bulk_update_lead_status(
    lead_ids: str = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    allowed_statuses = {
        "new",
        "drafted",
        "contacted",
        "replied",
        "not_interested",
        "not_fit",
        "delivery_failed",
    }
    if status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid lead status")
    ids = parse_lead_ids(lead_ids)
    if not ids:
        raise HTTPException(status_code=400, detail="No leads selected")

    updated = 0
    now = datetime.utcnow()
    leads = list(db.query(Lead).filter(Lead.id.in_(ids)).all())
    for lead in leads:
        lead.status = status
        if status == "contacted":
            lead.last_contacted_at = now
        updated += 1

    if status == "contacted":
        events = db.query(ContactEvent).filter(ContactEvent.lead_id.in_(ids), ContactEvent.status == "draft").all()
        for event in events:
            event.status = "sent"

    db.commit()
    return {"updated": updated, "status": status}


@app.post("/api/leads/{lead_id}/delete")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.execute(delete(ContactEvent).where(ContactEvent.lead_id == lead_id))
    db.delete(lead)
    db.commit()
    return {"deleted": True, "lead_id": lead_id}


@app.post("/api/outreach")
def draft_outreach(lead_id: int = Form(...), channel: str = Form(...), step: str = Form("initial"), db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    event = create_draft_for_lead(db, lead, channel, step)
    db.commit()
    db.refresh(event)
    return serialize_event(event, lead)


@app.post("/api/outreach/bulk")
def bulk_draft_outreach(
    lead_ids: str = Form(...),
    channel: str = Form(...),
    step: str = Form("initial"),
    db: Session = Depends(get_db),
):
    ids = []
    for raw_id in lead_ids.split(","):
        raw_id = raw_id.strip()
        if raw_id:
            try:
                ids.append(int(raw_id))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid lead id: {raw_id}") from None
    if not ids:
        raise HTTPException(status_code=400, detail="No leads selected")
    if len(ids) > 50:
        raise HTTPException(status_code=400, detail="Bulk draft limit is 50 leads")

    created = []
    skipped = []
    for lead_id in ids:
        lead = db.get(Lead, lead_id)
        if not lead:
            skipped.append({"lead_id": lead_id, "reason": "not_found"})
            continue
        event = create_draft_for_lead(db, lead, channel, step)
        created.append((event, lead))

    db.commit()
    results = []
    for event, lead in created:
        db.refresh(event)
        results.append(serialize_event(event, lead))
    return {"created": len(results), "skipped": skipped, "drafts": results}


@app.post("/outreach")
def form_outreach(lead_id: int = Form(...), channel: str = Form(...), step: str = Form("initial"), db: Session = Depends(get_db)):
    draft_outreach(lead_id, channel, step, db)
    return RedirectResponse("/", status_code=303)


@app.post("/api/outreach/{event_id}")
def update_outreach_event(
    event_id: int,
    subject: str | None = Form(None),
    body: str = Form(...),
    db: Session = Depends(get_db),
):
    event = db.get(ContactEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Draft not found")
    event.subject = subject or None
    event.body = body
    db.commit()
    db.refresh(event)
    return {"event_id": event.id, "subject": event.subject, "body": event.body, "status": event.status}


@app.post("/api/outreach/{event_id}/sent")
def mark_outreach_sent(event_id: int, db: Session = Depends(get_db)):
    event = db.get(ContactEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Draft not found")
    lead = db.get(Lead, event.lead_id)
    event.status = "sent"
    if lead:
        lead.status = "contacted"
        lead.last_contacted_at = datetime.utcnow()
    db.commit()
    return {"event_id": event.id, "status": event.status, "lead_status": lead.status if lead else None}


@app.post("/api/outreach/{event_id}/send-whatsapp")
async def send_whatsapp_outreach(event_id: int, db: Session = Depends(get_db)):
    event = db.get(ContactEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Draft not found")
    lead = db.get(Lead, event.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if event.channel != "whatsapp":
        raise HTTPException(status_code=400, detail="Only WhatsApp drafts can be sent through this endpoint")
    limit_decision = check_whatsapp_send_limits(db, lead)
    if not limit_decision.allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "WhatsApp send limit reached",
                "reason": limit_decision.reason,
                "retry_after_seconds": limit_decision.retry_after_seconds,
            },
        )
    try:
        result = await send_whatsapp_template_via_chatwoot(lead, event)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        event.status = "failed"
        lead.status = "delivery_failed"
        db.commit()
        raise HTTPException(status_code=502, detail=f"Chatwoot send failed: {type(exc).__name__}") from exc

    apply_send_result(db, lead, event, result.status)
    return {
        "event_id": event.id,
        "lead_id": lead.id,
        "status": result.status,
        "lead_status": lead.status,
        "dry_run": result.dry_run,
        "detail": result.detail,
        "payload": result.payload,
        "response": result.response,
    }
