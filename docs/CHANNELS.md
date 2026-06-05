# Canales de contacto

## Estado actual

El sistema crea drafts individuales o masivos. Todavia no envia automaticamente. Esto es intencional: antes de activar envios conviene validar calidad de leads, copy, limites y cumplimiento.

## Flujo recomendado

1. Buscar/enriquecer leads.
2. Seleccionar leads A/B.
3. Crear drafts masivos por canal y paso.
4. Revisar una muestra de mensajes.
5. Enviar con proveedor conectado.
6. Guardar estado `sent`, `replied`, `interested`, `demo_booked`, `not_now` o `bad_fit`.

## Gmail

Uso recomendado: bajo volumen y mensajes muy personalizados.

Requisitos:

- Google Cloud project.
- Gmail API habilitada.
- OAuth consent screen.
- OAuth client desktop/web.
- Permiso `gmail.send`.
- SPF/DKIM/DMARC del dominio si se usa Google Workspace.

Limites practicos:

- No usar Gmail personal para volumen.
- Empezar con 20-40 emails/dia por cuenta.
- Incluir opt-out claro.
- Evitar adjuntos y links excesivos.

Integracion sugerida:

- Backend crea `ContactEvent` en estado `draft`.
- Boton futuro `Enviar email` llama a un sender Gmail.
- Si Gmail responde OK, evento pasa a `sent` y lead a `contacted`.
- Si falla, evento pasa a `failed` con error.

## WhatsApp

Uso recomendado: comercios con telefono/WhatsApp comercial publico.

Opciones:

- WhatsApp Business Cloud API de Meta.
- Twilio WhatsApp.
- Zenvia.
- Wati.

Notas importantes:

- Para conversaciones iniciadas por la empresa normalmente se usan templates aprobados.
- Para mensajes libres hay ventanas de conversacion despues de que el usuario responde.
- No conviene automatizar desde WhatsApp Web.
- Hay que cuidar opt-out y frecuencia.

Integracion sugerida:

- Crear drafts personalizados.
- Enviar solo leads con telefono/WhatsApp valido.
- Registrar `provider_message_id`.
- Escuchar webhooks de respuesta y actualizar estado.

## Instagram y LinkedIn

Para el MVP conviene semi-manual:

- Crear draft.
- Copiar.
- Enviar desde cuenta real.
- Marcar como enviado.

Automatizar DMs agresivamente suele bloquear cuentas y bajar calidad. Si se automatiza, hacerlo con herramientas oficiales o con limites muy conservadores.

## Secuencias

Primer contacto:

- Email si hay email comercial.
- WhatsApp si hay numero comercial y el rubro opera por WhatsApp.
- Instagram para comercios muy activos en redes.

Follow-ups:

- No insistir por todos los canales a la vez.
- Maximo 2 follow-ups sin respuesta.
- Cierre amable.

## Proximo paso tecnico

Crear una carpeta `app/senders` con proveedores:

- `gmail.py`
- `whatsapp.py`
- `manual.py`

Cada sender deberia implementar:

```python
send(event, lead) -> SendResult
```

El dashboard deberia mostrar:

- Crear draft.
- Copiar.
- Marcar enviado manualmente.
- Enviar por proveedor cuando este configurado.
