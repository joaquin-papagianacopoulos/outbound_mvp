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

### Templates recomendados para ENVI

Los drafts de WhatsApp del dashboard estan pensados para apuntar a templates aprobados. Crear estos nombres en WhatsApp Manager o en el proveedor:

`envi_diagnostico_inicial_v1`

```text
Hola {{1}}, soy {{2}} de {{3}}. Vi el contacto de {{1}} en Google Maps y queria hacerte una consulta puntual. En {{3}}, un sistema de gestion para comercios, ayudamos a ordenar stock, ventas y facturacion. Por lo que vimos, hoy manejan {{4}}. Lo tienen centralizado en un sistema o lo manejan separado? Si no corresponde, respondeme NO y no te escribo mas.
```

Variables:

- `{{1}}`: nombre del comercio
- `{{2}}`: nombre del vendedor
- `{{3}}`: ENVI
- `{{4}}`: senal detectada, por ejemplo `venta online` o `catalogo o stock amplio`

`envi_diagnostico_followup_1_v1`

```text
Hola {{1}}, soy {{2}} de {{3}}. Te escribo de nuevo porque en comercios con {{4}} suele pasar que stock, ventas y facturacion quedan separados. Si no corresponde, respondeme NO y no te escribo mas.
```

`envi_diagnostico_followup_2_v1`

```text
Hola {{1}}, ultima consulta rapida sobre {{2}}: cuando entra una venta por mostrador o WhatsApp, el stock se descuenta automaticamente o alguien lo carga despues? Si no corresponde, respondeme NO y no te escribo mas.
```

`envi_diagnostico_cierre_v1`

```text
Cierro por aca para no insistir, {{1}}. Si mas adelante quieren ordenar stock, ventas y facturacion con {{2}}, me escribis y te paso una demo corta. Respondeme NO si preferis que no te contactemos mas.
```

Categoria probable: marketing. Usar ejemplos reales al enviarlos a aprobacion.

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

## Integracion MVP implementada

El MVP ya tiene un sender para WhatsApp via Chatwoot en `app/channels/chatwoot.py`.

Por seguridad corre en dry-run por defecto:

```env
CHATWOOT_DRY_RUN=true
```

En dry-run el dashboard arma el payload completo pero no envia el mensaje.

Para envio real configurar:

```env
CHATWOOT_DRY_RUN=false
CHATWOOT_BASE_URL=https://tu-chatwoot.com
CHATWOOT_ACCOUNT_ID=1
CHATWOOT_API_ACCESS_TOKEN=token_de_usuario_o_admin
CHATWOOT_INBOX_IDENTIFIER=identificador_del_inbox_whatsapp
```

Flujo:

1. Crear draft con canal `whatsapp`.
2. El draft debe empezar con `WHATSAPP_TEMPLATE_DRAFT`.
3. El dashboard muestra boton `Enviar WhatsApp`.
4. El backend parsea template, language y variables.
5. Crea/contacta el contacto en Chatwoot.
6. Crea conversacion.
7. Crea mensaje con `template_params`.

Payload de mensaje esperado:

```json
{
  "content": "preview renderizado",
  "message_type": "outgoing",
  "private": false,
  "template_params": {
    "name": "envi_diagnostico_inicial_v1",
    "category": "MARKETING",
    "language": "es_AR",
    "processed_params": {
      "1": "Ferreteria Demo",
      "2": "Joaquin",
      "3": "ENVI",
      "4": "stock, ventas y facturacion"
    }
  }
}
```

Antes de apagar dry-run, confirmar en Chatwoot:

- El inbox es WhatsApp oficial.
- Los templates existen y estan aprobados.
- El `language` coincide con el aprobado.
- El orden de variables coincide con Meta.
- El token tiene permisos para crear contactos, conversaciones y mensajes.
