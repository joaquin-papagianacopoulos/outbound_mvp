# ENVI Outbound Automation MVP

## Critica pragmatica del diseño

El riesgo principal no es tecnico: es conseguir datos confiables sin romper terminos de servicio ni destruir entregabilidad. Google Maps, Instagram y directorios cambian markup, bloquean automatizacion y pueden limitar scraping. Para un MVP de 7 dias conviene usar APIs o proveedores con contrato: SerpAPI/Google Places para Maps, Apollo para personas/empresas B2B, Apify solo con actores mantenidos, y crawling propio solamente sobre sitios publicos de los comercios.

El segundo riesgo es confundir "mas leads" con "mas revenue". ENVI necesita comercios con dolor operativo real: stock, canales, sucursales, facturacion y control. Por eso el sistema prioriza senales de complejidad y genera mensajes por evidencia, no por rubro solamente.

El tercer riesgo es outreach. Enviar automaticamente email/WhatsApp/DM desde el dia 1 puede quemar dominios, numeros y cuentas. El MVP genera drafts, tracking y secuencias; el envio debe activarse despues con limites, opt-out, dominios separados, warming y revision de calidad.

## Arquitectura

1. Discovery: conectores por fuente normalizan candidatos a `LeadIn`.
2. Storage: SQLAlchemy sobre SQLite local o Postgres/Supabase via `DATABASE_URL`.
3. Deduplicacion: dominio, email o telefono normalizado.
4. Enrichment: crawler liviano del website publico; extrae email, telefonos, Instagram, WhatsApp y senales.
5. Scoring: reglas auditables + IA opcional.
6. Personalizacion: mensajes por canal y paso de secuencia, con IA opcional.
7. CRM: `leads` + `contact_events`, estados y tracking basico.
8. Dashboard: FastAPI + Jinja, suficiente para operar el MVP.

## Stack elegido

Python + FastAPI: rapido para APIs, jobs y scraping liviano.

SQLAlchemy + Postgres/Supabase: SQLite local para demo, Postgres cuando haya volumen y usuarios.

httpx + BeautifulSoup: crawling publico barato y controlable.

SerpAPI opcional: evita scraping directo de Google Maps para el MVP.

OpenAI opcional: scoring y personalizacion con fallback deterministico para no bloquear el sistema.

N8N recomendado fase 2: orquestacion visual de envios, delays, webhooks y CRM events sin construir scheduler propio.

Apify recomendado despues del MVP: actores mantenidos para fuentes fragiles como Instagram/directorios.

## Scoring base

- +2 negocio fisico
- +2 ecommerce
- +2 multisucursal
- +1 MercadoLibre
- +2 stock complejo
- +1 WhatsApp commerce
- +1 web profesional
- +0.5 canal contactable
- +1 industria ICP

Prioridad A: score >= 7. Prioridad B: score >= 4. Prioridad C: resto.

## Secuencia outbound

Dia 0: contacto inicial con observacion concreta.

Dia 2: follow-up sobre dolor operativo detectado.

Dia 5: pregunta corta de diagnostico.

Dia 9: cierre amable.

Reglas: maximo 1 canal primario por lead al inicio, no mas de 2 follow-ups si no hay senal, opt-out en email, no automatizar DMs desde cuentas nuevas, no enviar a contactos personales sensibles.

## Roadmap

Semana 1: validar rubros y ciudades, 300 leads, revisar 50 mensajes, medir respuestas.

Semana 2: integrar N8N + proveedor de email, health checks de dominio, suppression list y bounce tracking.

Semana 3: Apollo/Apify, enrichment de sucursales, deteccion de tecnologia ecommerce, dashboard por cohortes.

Semana 4: lead routing, A/B tests por rubro, feedback loop de replies al scoring.
