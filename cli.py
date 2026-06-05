import argparse
import asyncio
from pathlib import Path

from app.db import SessionLocal, init_db
from app.pipeline import import_csv
from app.repository import list_leads


async def main() -> None:
    parser = argparse.ArgumentParser(description="ENVI outbound MVP CLI")
    parser.add_argument("--import-csv", type=Path)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    init_db()
    with SessionLocal() as db:
        if args.import_csv:
            leads = await import_csv(db, args.import_csv)
            print(f"Imported and scored {len(leads)} leads")
        if args.list:
            for lead in list_leads(db, limit=50):
                print(f"{lead.priority} {lead.fit_score:>4} | {lead.business_name} | {lead.website or ''}")


if __name__ == "__main__":
    asyncio.run(main())
