# ENVI Outbound MVP

MVP local para discovery, enrichment, scoring, personalizacion y CRM liviano de leads B2B.

## Ejecutar

```powershell
cd C:\Users\joaqu\OneDrive\Desktop\DATOS\distribuidora-app\outbound_mvp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

Abrir `http://127.0.0.1:8000`.

## Importar CSV

Columnas soportadas:

```csv
business_name,industry,country,city,source,website,email,phone,whatsapp,instagram,address
```

Tambien se puede correr:

```powershell
python cli.py --import-csv sample_leads.csv --list
```

## Discovery por Google Maps

Configurar `SERPAPI_KEY` en `.env`. El endpoint `/discover` usa SerpAPI Google Maps y guarda los resultados.

## IA

Configurar `OPENAI_API_KEY` para AI scoring y personalizacion. Sin key, el sistema funciona con reglas y templates deterministicas.

## Drafts y campanias

Desde el dashboard se puede crear un draft individual por lead o seleccionar varios leads y crear drafts masivos para el mismo canal/paso.

Los drafts no se envian automaticamente. Se pueden revisar, editar, copiar y marcar como enviados. La guia para conectar Gmail, WhatsApp y otros canales esta en `docs/CHANNELS.md`.

## Produccion

Cambiar:

```env
DATABASE_URL=postgresql+psycopg://user:password@host:5432/db
```

En Supabase conviene usar Postgres directo desde backend, no la anon key del frontend.
