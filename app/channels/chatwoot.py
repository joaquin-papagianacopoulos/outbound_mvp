import re
from dataclasses import dataclass

import httpx

from app.channels.whatsapp_template import build_chatwoot_template_params, parse_whatsapp_template_draft
from app.config import get_settings
from app.models import ContactEvent, Lead


@dataclass
class SendResult:
    ok: bool
    status: str
    provider: str
    dry_run: bool
    detail: str
    payload: dict
    response: dict | None = None


def normalize_whatsapp_phone(lead: Lead) -> str | None:
    raw = lead.whatsapp or lead.phone
    if not raw:
        return None
    digits = re.sub(r"\D+", "", raw)
    if len(digits) < 8:
        return None
    if raw.strip().startswith("+"):
        return "+" + digits
    if digits.startswith("54"):
        return "+" + digits
    return "+" + digits


def build_chatwoot_payload(lead: Lead, event: ContactEvent) -> dict:
    draft = parse_whatsapp_template_draft(event.body)
    phone = normalize_whatsapp_phone(lead)
    if not phone:
        raise ValueError("Lead has no valid phone/WhatsApp number")

    return {
        "contact": {
            "name": lead.business_name,
            "phone_number": phone,
            "identifier": phone,
            "custom_attributes": {
                "lead_id": lead.id,
                "source": lead.source,
                "fit_score": lead.fit_score,
                "priority": lead.priority,
            },
        },
        "message": {
            "content": draft.rendered_message,
            "message_type": "outgoing",
            "private": False,
            "template_params": build_chatwoot_template_params(draft),
        },
    }


async def send_whatsapp_template_via_chatwoot(lead: Lead, event: ContactEvent) -> SendResult:
    settings = get_settings()
    payload = build_chatwoot_payload(lead, event)

    if settings.chatwoot_dry_run:
        return SendResult(
            ok=True,
            status="dry_run",
            provider="chatwoot",
            dry_run=True,
            detail="Dry run: no message was sent",
            payload=payload,
        )

    missing = [
        name
        for name, value in {
            "CHATWOOT_BASE_URL": settings.chatwoot_base_url,
            "CHATWOOT_ACCOUNT_ID": settings.chatwoot_account_id,
            "CHATWOOT_API_ACCESS_TOKEN": settings.chatwoot_api_access_token,
            "CHATWOOT_INBOX_IDENTIFIER": settings.chatwoot_inbox_identifier,
        }.items()
        if not value
    ]
    if missing:
        return SendResult(
            ok=False,
            status="config_error",
            provider="chatwoot",
            dry_run=False,
            detail=f"Missing config: {', '.join(missing)}",
            payload=payload,
        )

    base_url = settings.chatwoot_base_url.rstrip("/")
    headers = {
        "Content-Type": "application/json",
        "api_access_token": settings.chatwoot_api_access_token,
    }

    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        contact_url = f"{base_url}/public/api/v1/inboxes/{settings.chatwoot_inbox_identifier}/contacts"
        contact_response = await client.post(contact_url, json=payload["contact"])
        contact_response.raise_for_status()
        contact_data = contact_response.json()
        contact_identifier = contact_data.get("source_id") or payload["contact"]["identifier"]

        conversation_url = f"{base_url}/public/api/v1/inboxes/{settings.chatwoot_inbox_identifier}/contacts/{contact_identifier}/conversations"
        conversation_response = await client.post(conversation_url, json={"custom_attributes": {"lead_id": lead.id}})
        conversation_response.raise_for_status()
        conversation_data = conversation_response.json()
        conversation_id = conversation_data.get("id")

        message_url = f"{base_url}/api/v1/accounts/{settings.chatwoot_account_id}/conversations/{conversation_id}/messages"
        message_response = await client.post(message_url, json=payload["message"])
        message_response.raise_for_status()
        message_data = message_response.json()

    return SendResult(
        ok=True,
        status="sent",
        provider="chatwoot",
        dry_run=False,
        detail="WhatsApp template sent via Chatwoot",
        payload=payload,
        response={
            "contact": contact_data,
            "conversation": conversation_data,
            "message": message_data,
        },
    )
