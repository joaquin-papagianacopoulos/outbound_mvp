from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Lead


@dataclass
class OutreachLimitDecision:
    allowed: bool
    reason: str | None = None
    retry_after_seconds: int | None = None


def check_whatsapp_send_limits(db: Session, lead: Lead) -> OutreachLimitDecision:
    settings = get_settings()
    now = datetime.utcnow()

    if lead.last_contacted_at:
        lead_cooldown = timedelta(hours=settings.whatsapp_lead_cooldown_hours)
        next_allowed_at = lead.last_contacted_at + lead_cooldown
        if now < next_allowed_at:
            retry_after = int((next_allowed_at - now).total_seconds())
            return OutreachLimitDecision(
                allowed=False,
                reason=f"Lead cooldown active. Last contacted at {lead.last_contacted_at.isoformat()} UTC",
                retry_after_seconds=retry_after,
            )

    last_send_at = db.scalar(select(func.max(Lead.last_contacted_at)).where(Lead.last_contacted_at.is_not(None)))
    if last_send_at:
        next_allowed_at = last_send_at + timedelta(seconds=settings.whatsapp_min_seconds_between_sends)
        if now < next_allowed_at:
            retry_after = int((next_allowed_at - now).total_seconds())
            return OutreachLimitDecision(
                allowed=False,
                reason=f"Global send pacing active. Last send at {last_send_at.isoformat()} UTC",
                retry_after_seconds=retry_after,
            )

    day_start = now - timedelta(days=1)
    day_count = db.scalar(select(func.count(Lead.id)).where(Lead.last_contacted_at >= day_start)) or 0
    if day_count >= settings.whatsapp_max_sends_per_day:
        return OutreachLimitDecision(
            allowed=False,
            reason=f"Daily WhatsApp limit reached: {day_count}/{settings.whatsapp_max_sends_per_day}",
            retry_after_seconds=3600,
        )

    hour_start = now - timedelta(hours=1)
    hour_count = db.scalar(select(func.count(Lead.id)).where(Lead.last_contacted_at >= hour_start)) or 0
    if hour_count >= settings.whatsapp_max_sends_per_hour:
        return OutreachLimitDecision(
            allowed=False,
            reason=f"Hourly WhatsApp limit reached: {hour_count}/{settings.whatsapp_max_sends_per_hour}",
            retry_after_seconds=900,
        )

    return OutreachLimitDecision(allowed=True)
