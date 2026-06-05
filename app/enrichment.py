import json
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.models import Lead
from app.utils import first_email, phones

SIGNAL_PATTERNS = {
    "ecommerce": [
        "comprar", "comprá", "carrito", "checkout", "tienda online", "comprá online",
        "compra online", "envios a todo el pais", "envíos a todo el país",
    ],
    "stock_complexity": [
        "consultar stock", "consulta stock", "consultá stock", "sin stock", "stock disponible",
        "catalogo", "catálogo", "sku", "mayorista",
    ],
    "multibranch": [
        "sucursales", "nuestras sucursales", "casa central", "locales", "showrooms",
    ],
    "whatsapp_commerce": [
        "whatsapp", "wa.me", "api.whatsapp.com", "pedidos por whatsapp",
    ],
}

PROFESSIONAL_WEB_MARKERS = [
    "shopify", "woocommerce", "tiendanube", "vtex", "mercadoshops", "facebook-domain-verification",
    "google tag manager", "gtm-", "analytics",
]


def _clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))


def _extract_socials(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    socials = {}
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, anchor["href"])
        low = href.lower()
        if "instagram.com/" in low and "instagram" not in socials:
            socials["instagram"] = href
        if "linkedin.com/" in low and "linkedin" not in socials:
            socials["linkedin"] = href
        if ("wa.me/" in low or "api.whatsapp.com" in low) and "whatsapp" not in socials:
            socials["whatsapp"] = href
    return socials


async def enrich_lead(lead: Lead) -> Lead:
    if not lead.website:
        lead.signals_json = json.dumps(existing_signals(lead), ensure_ascii=True)
        return lead

    url = lead.website
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True, headers={"User-Agent": "ENVI lead research bot; contact: ventas"}) as client:
            response = await client.get(url)
            response.raise_for_status()
    except Exception as exc:
        signals = existing_signals(lead) + [f"website_fetch_failed:{type(exc).__name__}"]
        lead.signals_json = json.dumps(sorted(set(signals)), ensure_ascii=True)
        return lead

    html = response.text[:750_000]
    text = _clean_text(html)
    corpus = (html + " " + text).lower()
    signals = existing_signals(lead)

    email = first_email(text)
    if email and not lead.email:
        lead.email = email

    found_phones = phones(text)
    if found_phones and not lead.phone:
        lead.phone = found_phones[0]

    socials = _extract_socials(html, url)
    for key, value in socials.items():
        if not getattr(lead, key, None):
            setattr(lead, key, value)

    for group, patterns in SIGNAL_PATTERNS.items():
        if any(pattern in corpus for pattern in patterns):
            signals.append(group)

    if any(marker in corpus for marker in PROFESSIONAL_WEB_MARKERS):
        lead.web_professional = True
        signals.append("web_professional")

    branch_mentions = len(re.findall(r"\bsucursal(?:es)?\b|\blocal(?:es)?\b", corpus))
    if branch_mentions >= 2:
        lead.branches_estimate = max(lead.branches_estimate or 0, 2)
        signals.append("possible_multibranch")

    lead.has_ecommerce = lead.has_ecommerce or "ecommerce" in signals
    lead.has_whatsapp_commerce = lead.has_whatsapp_commerce or "whatsapp_commerce" in signals or bool(lead.whatsapp)
    lead.signals_json = json.dumps(sorted(set(signals)), ensure_ascii=True)
    return lead


def existing_signals(lead: Lead) -> list[str]:
    try:
        return json.loads(lead.signals_json or "[]")
    except json.JSONDecodeError:
        return []
