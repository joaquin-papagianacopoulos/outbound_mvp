from dataclasses import dataclass


@dataclass
class WhatsAppTemplateDraft:
    template_name: str
    language: str
    step: str
    variables: dict[str, str]
    rendered_message: str


def parse_whatsapp_template_draft(body: str) -> WhatsAppTemplateDraft:
    lines = body.splitlines()
    if not lines or lines[0].strip() != "WHATSAPP_TEMPLATE_DRAFT":
        raise ValueError("Draft is not a WhatsApp template draft")

    template_name = ""
    language = "es_AR"
    step = "initial"
    variables: dict[str, str] = {}
    rendered_lines: list[str] = []
    mode = "header"

    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "variables:":
            mode = "variables"
            continue
        if stripped == "rendered_message:":
            mode = "rendered"
            continue
        if mode == "rendered":
            rendered_lines.append(line)
            continue
        if mode == "variables" and "=" in stripped:
            key, value = stripped.split("=", 1)
            variables[key.strip()] = value.strip()
            continue
        if mode == "header" and "=" in stripped:
            key, value = stripped.split("=", 1)
            if key == "template_name":
                template_name = value.strip()
            elif key == "language":
                language = value.strip()
            elif key == "step":
                step = value.strip()

    if not template_name:
        raise ValueError("Missing WhatsApp template_name")

    return WhatsAppTemplateDraft(
        template_name=template_name,
        language=language,
        step=step,
        variables=variables,
        rendered_message="\n".join(rendered_lines).strip(),
    )


def build_chatwoot_template_params(draft: WhatsAppTemplateDraft) -> dict:
    return {
        "name": draft.template_name,
        "category": "MARKETING",
        "language": draft.language,
        "processed_params": draft.variables,
    }
