import re
from urllib.parse import urlparse


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?:\+?\d[\s().-]?){8,18}")


def normalize_domain(url: str | None) -> str | None:
    if not url:
        return None
    value = url.strip()
    if not value:
        return None
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    host = urlparse(value).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host or None


def normalize_email(email: str | None) -> str | None:
    return email.strip().lower() if email else None


def normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    digits = re.sub(r"\D+", "", phone)
    return digits[-12:] if len(digits) >= 8 else None


def first_email(text: str) -> str | None:
    match = EMAIL_RE.search(text or "")
    return match.group(0).lower() if match else None


def phones(text: str) -> list[str]:
    found = []
    for match in PHONE_RE.findall(text or ""):
        digits = normalize_phone(match)
        if digits and digits not in found:
            found.append(digits)
    return found
