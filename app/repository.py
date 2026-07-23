import json

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Lead
from app.schemas import LeadIn
from app.utils import normalize_domain, normalize_email, normalize_phone


def upsert_lead(db: Session, data: LeadIn | dict) -> Lead:
    payload = data.model_dump() if hasattr(data, "model_dump") else dict(data)
    domain = normalize_domain(payload.get("website"))
    email = normalize_email(payload.get("email"))
    phone = normalize_phone(payload.get("phone") or payload.get("whatsapp"))

    clauses = []
    if domain:
        clauses.append(Lead.normalized_domain == domain)
    if email:
        clauses.append(Lead.normalized_email == email)
    if phone:
        clauses.append(Lead.normalized_phone == phone)

    lead = None
    if clauses:
        lead = db.execute(select(Lead).where(or_(*clauses))).scalar_one_or_none()

    if not lead:
        lead = Lead(business_name=payload["business_name"])
        db.add(lead)

    for key, value in payload.items():
        if value not in (None, "") and hasattr(lead, key):
            setattr(lead, key, value)
    lead.normalized_domain = domain or lead.normalized_domain
    lead.normalized_email = email or lead.normalized_email
    lead.normalized_phone = phone or lead.normalized_phone

    db.commit()
    db.refresh(lead)
    return lead


def find_existing_lead(db: Session, data: LeadIn | dict) -> Lead | None:
    payload = data.model_dump() if hasattr(data, "model_dump") else dict(data)
    domain = normalize_domain(payload.get("website"))
    email = normalize_email(payload.get("email"))
    phone = normalize_phone(payload.get("phone") or payload.get("whatsapp"))
    clauses = []
    if domain:
        clauses.append(Lead.normalized_domain == domain)
    if email:
        clauses.append(Lead.normalized_email == email)
    if phone:
        clauses.append(Lead.normalized_phone == phone)
    if not clauses:
        return None
    return db.execute(select(Lead).where(or_(*clauses))).scalar_one_or_none()


def list_leads(db: Session, limit: int = 100, status: str | None = None, filters: dict | None = None) -> list[Lead]:
    stmt = select(Lead)
    if status:
        stmt = stmt.where(Lead.status == status)
    filters = filters or {}
    if filters.get("has_web"):
        stmt = stmt.where(Lead.website.is_not(None), Lead.website != "")
    if filters.get("has_email"):
        stmt = stmt.where(Lead.email.is_not(None), Lead.email != "")
    if filters.get("has_phone"):
        stmt = stmt.where(Lead.phone.is_not(None), Lead.phone != "")
    if filters.get("has_whatsapp"):
        stmt = stmt.where(Lead.whatsapp.is_not(None), Lead.whatsapp != "")
    if filters.get("has_instagram"):
        stmt = stmt.where(Lead.instagram.is_not(None), Lead.instagram != "")
    if filters.get("has_ecommerce"):
        stmt = stmt.where(Lead.has_ecommerce.is_(True))
    if filters.get("has_multibranch"):
        stmt = stmt.where(Lead.branches_estimate.is_not(None), Lead.branches_estimate >= 2)
    if filters.get("priority"):
        stmt = stmt.where(Lead.priority == filters["priority"])
    if filters.get("city"):
        stmt = stmt.where(Lead.city.ilike(f"%{filters['city']}%"))
    if filters.get("industry"):
        stmt = stmt.where(Lead.industry.ilike(f"%{filters['industry']}%"))
    stmt = stmt.order_by(Lead.fit_score.desc(), Lead.created_at.desc()).limit(limit)
    return list(db.execute(stmt).scalars())


def lead_matches_filters(lead: Lead, filters: dict | None = None) -> bool:
    filters = filters or {}
    checks = [
        (filters.get("has_web"), bool(lead.website)),
        (filters.get("has_email"), bool(lead.email)),
        (filters.get("has_phone"), bool(lead.phone)),
        (filters.get("has_whatsapp"), bool(lead.whatsapp)),
        (filters.get("has_instagram"), bool(lead.instagram)),
        (filters.get("has_ecommerce"), bool(lead.has_ecommerce)),
        (filters.get("has_multibranch"), bool(lead.branches_estimate and lead.branches_estimate >= 2)),
    ]
    if any(required and not actual for required, actual in checks):
        return False
    if filters.get("priority") and lead.priority != filters["priority"]:
        return False
    if filters.get("city") and filters["city"].lower() not in (lead.city or "").lower():
        return False
    if filters.get("industry") and filters["industry"].lower() not in (lead.industry or "").lower():
        return False
    return True


def stats(db: Session) -> dict:
    total = db.execute(select(func.count(Lead.id))).scalar() or 0
    avg_score = db.execute(select(func.avg(Lead.fit_score))).scalar() or 0
    by_priority = db.execute(select(Lead.priority, func.count(Lead.id)).group_by(Lead.priority)).all()
    by_source = db.execute(select(Lead.source, func.count(Lead.id)).group_by(Lead.source)).all()
    by_city = db.execute(select(Lead.city, func.count(Lead.id)).group_by(Lead.city)).all()
    by_status = db.execute(select(Lead.status, func.count(Lead.id)).group_by(Lead.status)).all()
    replied = db.execute(select(func.count(Lead.id)).where(Lead.status == "replied")).scalar() or 0
    return {
        "total": total,
        "avg_score": round(float(avg_score), 2),
        "reply_rate": round((replied / total) * 100, 2) if total else 0,
        "by_priority": dict(by_priority),
        "by_source": dict(by_source),
        "by_city": dict(by_city),
        "by_status": dict(by_status),
    }


def lead_signals(lead: Lead) -> list[str]:
    try:
        return json.loads(lead.signals_json or "[]")
    except json.JSONDecodeError:
        return []
