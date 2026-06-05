import json

from openai import OpenAI

from app.config import get_settings
from app.models import Lead
from app.repository import lead_signals


def score_with_rules(lead: Lead) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    signals = set(lead_signals(lead))

    def add(points: float, reason: str) -> None:
        nonlocal score
        score += points
        reasons.append(f"+{points:g} {reason}")

    industry_bonus = {
        "ferreteria", "ferretería", "repuestos", "repuestera", "pet shop", "bazar",
        "perfumeria", "perfumería", "ropa", "electricidad", "dietetica", "dietética",
    }
    if (lead.industry or "").lower() in industry_bonus:
        add(1, "industria ICP")
    if lead.has_physical_store:
        add(2, "negocio fisico")
    if lead.has_ecommerce or "ecommerce" in signals:
        add(2, "ecommerce / compra online")
    if lead.branches_estimate and lead.branches_estimate >= 2:
        add(2, "posible multisucursal")
    elif "multibranch" in signals or "possible_multibranch" in signals:
        add(2, "senales de varias sucursales")
    if "stock_complexity" in signals:
        add(2, "stock complejo")
    if lead.has_whatsapp_commerce or "whatsapp_commerce" in signals:
        add(1, "venta por WhatsApp")
    if lead.web_professional or "web_professional" in signals:
        add(1, "web profesional")
    if lead.email or lead.whatsapp or lead.instagram:
        add(0.5, "canal contactable")

    return min(score, 10), reasons


def priority(score: float) -> str:
    if score >= 7:
        return "A"
    if score >= 4:
        return "B"
    return "C"


def apply_rule_score(lead: Lead) -> Lead:
    score, reasons = score_with_rules(lead)
    lead.score_rules = score
    if lead.score_ai is None:
        lead.fit_score = score
    else:
        lead.fit_score = round((score * 0.7) + (lead.score_ai * 0.3), 2)
    lead.priority = priority(lead.fit_score)
    existing = lead_signals(lead)
    lead.signals_json = json.dumps(sorted(set(existing + reasons)), ensure_ascii=True)
    return lead


def apply_ai_score(lead: Lead) -> Lead:
    settings = get_settings()
    if not settings.openai_api_key:
        lead.ai_reason = "AI scoring skipped: OPENAI_API_KEY not configured"
        return lead

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = {
        "business_name": lead.business_name,
        "industry": lead.industry,
        "city": lead.city,
        "website": lead.website,
        "signals": lead_signals(lead),
        "rule_score": lead.score_rules,
    }
    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0.1,
        messages=[
            {
                "role": "system",
                "content": (
                    "Sos un analista B2B SaaS para comercios fisicos LATAM. "
                    "Devolve JSON estricto con score 1-10 y reason breve. "
                    "Penaliza si no hay evidencia concreta."
                ),
            },
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    try:
        data = json.loads(content)
        lead.score_ai = max(1, min(10, float(data.get("score", lead.score_rules))))
        lead.ai_reason = str(data.get("reason", ""))[:1000]
        lead.fit_score = round((lead.score_rules * 0.7) + (lead.score_ai * 0.3), 2)
        lead.priority = priority(lead.fit_score)
    except Exception:
        lead.ai_reason = "AI scoring failed to parse response"
    return lead
