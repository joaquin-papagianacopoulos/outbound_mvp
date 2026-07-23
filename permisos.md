# Permisos y limites de outreach

Estos limites controlan cuantos mensajes de WhatsApp puede enviar el dashboard cuando `CHATWOOT_DRY_RUN=false`.

Para modificarlos, editar el archivo `.env`:

```env
WHATSAPP_MAX_SENDS_PER_DAY=50
WHATSAPP_MAX_SENDS_PER_HOUR=10
WHATSAPP_MIN_SECONDS_BETWEEN_SENDS=120
WHATSAPP_LEAD_COOLDOWN_HOURS=72
```

Que hace cada uno:

- `WHATSAPP_MAX_SENDS_PER_DAY`: maximo de contactos enviados en las ultimas 24 horas.
- `WHATSAPP_MAX_SENDS_PER_HOUR`: maximo de contactos enviados en la ultima hora.
- `WHATSAPP_MIN_SECONDS_BETWEEN_SENDS`: pausa minima entre un envio y el siguiente.
- `WHATSAPP_LEAD_COOLDOWN_HOURS`: tiempo minimo antes de volver a contactar al mismo lead.

Recomendacion para produccion inicial:

- Empezar con 20 a 30 mensajes por dia.
- Subir a 50 por dia solo si no hay bloqueos, quejas o baja calidad de respuestas.
- Mantener `WHATSAPP_MIN_SECONDS_BETWEEN_SENDS` en 120 segundos o mas.
- No bajar `WHATSAPP_LEAD_COOLDOWN_HOURS` de 72 horas.

Si el dashboard responde con error `429`, significa que se alcanzo un limite y hay que esperar antes de seguir enviando.
