from openai import OpenAI

from app.config import get_settings
from app.models import Lead
from app.repository import lead_signals


SEQUENCE = {
    "initial": "primer contacto",
    "follow_up_1": "seguimiento con angulo operativo",
    "follow_up_2": "seguimiento corto con prueba de dolor",
    "breakup": "cierre amable",
}


WHATSAPP_TEMPLATE_BY_STEP = {
    "initial": "whatsapp_template_initial_name",
    "follow_up_1": "whatsapp_template_follow_up_1_name",
    "follow_up_2": "whatsapp_template_follow_up_2_name",
    "breakup": "whatsapp_template_breakup_name",
}


def lead_angle(lead: Lead) -> str:
    signals = set(lead_signals(lead))
    observed = []
    if lead.has_ecommerce or "ecommerce" in signals:
        observed.append("venta online")
    if lead.has_whatsapp_commerce or "whatsapp_commerce" in signals:
        observed.append("pedidos por WhatsApp")
    if lead.branches_estimate or "multibranch" in signals or "possible_multibranch" in signals:
        observed.append("mas de un local o sucursal")
    if "stock_complexity" in signals:
        observed.append("catalogo o stock amplio")
    return ", ".join(observed[:3]) if observed else "stock, ventas y facturacion"


def whatsapp_template_name(step: str) -> str:
    settings = get_settings()
    field = WHATSAPP_TEMPLATE_BY_STEP.get(step, WHATSAPP_TEMPLATE_BY_STEP["initial"])
    return getattr(settings, field)


def whatsapp_template_draft(lead: Lead, step: str) -> tuple[str, str]:
    settings = get_settings()
    business_name = lead.business_name
    sender_name = settings.outreach_from_name
    product = settings.outreach_product_name
    product_description = f"{product}, un sistema de gestion para comercios"
    angle = lead_angle(lead)
    template_name = whatsapp_template_name(step)
    language = settings.whatsapp_template_language

    if step == "follow_up_1":
        rendered = (
            f"Hola {business_name}, soy {sender_name} de {product}. "
            f"Te escribo de nuevo porque en comercios con {angle} suele pasar que "
            "stock, ventas y facturacion quedan separados. "
            "Si no corresponde, respondeme NO y no te escribo mas."
        )
        variables = [business_name, sender_name, product, angle]
    elif step == "follow_up_2":
        rendered = (
            f"Hola {business_name}, ultima consulta rapida sobre {product}: "
            "cuando entra una venta por mostrador o WhatsApp, el stock se descuenta automaticamente o alguien lo carga despues? "
            "Si no corresponde, respondeme NO y no te escribo mas."
        )
        variables = [business_name, product]
    elif step == "breakup":
        rendered = (
            f"Cierro por aca para no insistir, {business_name}. "
            f"Si mas adelante quieren ordenar stock, ventas y facturacion con {product}, me escribis y te paso una demo corta. "
            "Respondeme NO si preferis que no te contactemos mas."
        )
        variables = [business_name, product]
    else:
        rendered = (
            f"Hola {business_name}, soy {sender_name} de {product}. "
            f"Vi el contacto de {business_name} en Google Maps y queria hacerte una consulta puntual. "
            f"En {product_description}, ayudamos a ordenar stock, ventas y facturacion. "
            f"Por lo que vimos, hoy manejan {angle}. Lo tienen centralizado en un sistema o lo manejan separado? "
            "Si no corresponde, respondeme NO y no te escribo mas."
        )
        variables = [business_name, sender_name, product, angle]

    body = [
        "WHATSAPP_TEMPLATE_DRAFT",
        f"template_name={template_name}",
        f"language={language}",
        f"step={step}",
        "variables:",
    ]
    body.extend([f"  {index}={value}" for index, value in enumerate(variables, start=1)])
    body.extend(["", "rendered_message:", rendered])
    return f"whatsapp_template:{template_name}", "\n".join(body)


def deterministic_message(lead: Lead, channel: str, step: str) -> tuple[str | None, str]:
    if channel == "whatsapp":
        return whatsapp_template_draft(lead, step)

    angle = lead_angle(lead)
    name = lead.business_name
    product = get_settings().outreach_product_name

    if channel == "email":
        subject = f"{name} | stock, ventas y facturacion"
        body = (
            f"Hola, vi que {name} maneja {angle}.\n\n"
            f"Trabajo con {product}, un sistema de gestion para comercios que necesitan ordenar stock, ventas, facturacion y operacion diaria sin depender de planillas.\n\n"
            "Creo que puede tener sentido si hoy estan conciliando local fisico, WhatsApp/ecommerce y stock en mas de un canal.\n\n"
            "Tiene sentido que te mande 3 ideas concretas para mejorar esa operacion?"
        )
        if step != "initial":
            body = follow_up_body(name, angle, product, step)
        return subject, body

    body = (
        f"Hola, vi que {name} maneja {angle}. En {product} ayudamos a comercios fisicos a centralizar stock, ventas y facturacion. "
        "Te sirve que te mande una idea concreta para ordenar esa operacion?"
    )
    if channel == "instagram":
        body = f"Hola! Vi lo de {name} y me llamo la atencion que manejan {angle}. Les sirve una idea corta para ordenar stock/ventas sin planillas?"
    if channel == "linkedin":
        body = f"Hola, vi que {name} parece tener {angle}. Trabajo con comercios que necesitan centralizar stock, ventas y facturacion. Te puedo compartir una idea breve?"
    if step != "initial":
        _, emailish = deterministic_message(lead, "email", step)
        body = emailish.replace("\n\n", " ")
    return None, body


def follow_up_body(name: str, angle: str, product: str, step: str) -> str:
    if step == "follow_up_1":
        return (
            f"Hola, retomo por {name}.\n\n"
            f"Cuando un comercio combina {angle}, suele aparecer el mismo problema: stock desactualizado entre mostrador, WhatsApp y venta online.\n\n"
            f"{product} apunta justo a centralizar eso. Hoy lo resuelven con sistema o con planillas?"
        )
    if step == "follow_up_2":
        return (
            f"Hola, ultima consulta rapida: si manana cambia un precio o falta stock en {name}, "
            "lo actualizan en un solo lugar o canal por canal?"
        )
    return (
        f"Cierro por aca para no insistir. Si mas adelante {name} quiere ordenar stock, ventas y facturacion en un solo sistema, "
        "me escribis y te paso una propuesta concreta."
    )


def ai_message(lead: Lead, channel: str, step: str) -> tuple[str | None, str]:
    if channel == "whatsapp":
        return whatsapp_template_draft(lead, step)

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
                    "Escribi outbound B2B en espanol rioplatense/neutro LATAM. "
                    "Debe ser breve, especifico y no sonar masivo. No inventes senales. "
                    "Inclui opt-out suave si es email de seguimiento o cierre. "
                    "Devolve solo el cuerpo del mensaje."
                ),
            },
            {"role": "user", "content": str(prompt)},
        ],
    )
    return subject, (response.choices[0].message.content or fallback).strip()
