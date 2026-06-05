from openai import OpenAI

from app.config import get_settings
from app.models import Lead
from app.repository import lead_signals


SEQUENCE = {
    "initial": "primer contacto",
    "follow_up_1": "seguimiento con ángulo operativo",
    "follow_up_2": "seguimiento corto con prueba de dolor",
    "breakup": "cierre amable",
}


def deterministic_message(lead: Lead, channel: str, step: str) -> tuple[str | None, str]:
    signals = set(lead_signals(lead))
    observed = []
    if lead.has_ecommerce or "ecommerce" in signals:
        observed.append("venta online")
    if lead.has_whatsapp_commerce or "whatsapp_commerce" in signals:
        observed.append("pedidos por WhatsApp")
    if lead.branches_estimate or "multibranch" in signals or "possible_multibranch" in signals:
        observed.append("más de un local/sucursal")
    if "stock_complexity" in signals:
        observed.append("catálogo/stock amplio")
    angle = ", ".join(observed[:3]) if observed else "operación comercial física"

    name = lead.business_name
    product = get_settings().outreach_product_name

    if channel == "email":
        subject = f"{name} | stock, ventas y facturación"
        body = (
            f"Hola, vi que {name} maneja {angle}.\n\n"
            f"Trabajo con {product}, un sistema de gestión para comercios que necesitan ordenar stock, ventas, facturación y operación diaria sin depender de planillas.\n\n"
            "Creo que puede tener sentido si hoy están conciliando local físico, WhatsApp/ecommerce y stock en más de un canal.\n\n"
            "¿Tiene sentido que te mande 3 ideas concretas para mejorar esa operación?"
        )
        if step != "initial":
            body = follow_up_body(name, angle, product, step)
        return subject, body

    body = (
        f"Hola, vi que {name} maneja {angle}. En {product} ayudamos a comercios físicos a centralizar stock, ventas y facturación. "
        "¿Te sirve que te mande una idea concreta para ordenar esa operación?"
    )
    if channel == "instagram":
        body = f"Hola! Vi lo de {name} y me llamó la atención que manejan {angle}. ¿Les sirve una idea corta para ordenar stock/ventas sin planillas?"
    if channel == "linkedin":
        body = f"Hola, vi que {name} parece tener {angle}. Trabajo con comercios que necesitan centralizar stock, ventas y facturación. ¿Te puedo compartir una idea breve?"
    if step != "initial":
        _, emailish = deterministic_message(lead, "email", step)
        body = emailish.replace("\n\n", " ")
    return None, body


def follow_up_body(name: str, angle: str, product: str, step: str) -> str:
    if step == "follow_up_1":
        return (
            f"Hola, retomo por {name}.\n\n"
            f"Cuando un comercio combina {angle}, suele aparecer el mismo problema: stock desactualizado entre mostrador, WhatsApp y venta online.\n\n"
            f"{product} apunta justo a centralizar eso. ¿Hoy lo resuelven con sistema o con planillas?"
        )
    if step == "follow_up_2":
        return (
            f"Hola, última consulta rápida: si mañana cambia un precio o falta stock en {name}, "
            "¿lo actualizan en un solo lugar o canal por canal?"
        )
    return (
        f"Cierro por acá para no insistir. Si más adelante {name} quiere ordenar stock, ventas y facturación en un solo sistema, "
        "me escribís y te paso una propuesta concreta."
    )


def ai_message(lead: Lead, channel: str, step: str) -> tuple[str | None, str]:
    settings = get_settings()
    if not settings.openai_api_key:
        return deterministic_message(lead, channel, step)

    subject, fallback = deterministic_message(lead, channel, step)
    client = OpenAI(api_key=settings.openai_api_key)
    prompt = {
        "lead": {
            "business_name": lead.business_name,
            "industry": lead.industry,
            "city": lead.city,
            "website": lead.website,
            "signals": lead_signals(lead),
            "fit_score": lead.fit_score,
        },
        "channel": channel,
        "step": step,
        "sequence_context": SEQUENCE.get(step, step),
        "fallback": fallback,
    }
    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0.4,
        messages=[
            {
                "role": "system",
                "content": (
                    "Escribí outbound B2B en español rioplatense/neutro LATAM. "
                    "Debe ser breve, específico y no sonar masivo. No inventes señales. "
                    "Incluí opt-out suave si es email de seguimiento o cierre. "
                    "Devolve solo el cuerpo del mensaje."
                ),
            },
            {"role": "user", "content": str(prompt)},
        ],
    )
    return subject, (response.choices[0].message.content or fallback).strip()
