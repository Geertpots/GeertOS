# Sprint 8A — cloudbasis

Sprint 7 blijft standaard ongewijzigd met de lokale SQLite-database werken.

## Databasekeuze

- Zonder `GEERTOS_DATABASE_URL`: bestaande SQLite-database.
- Met `GEERTOS_DATABASE_URL`: standaard PostgreSQL, waaronder Supabase.
- De app gebruikt geen leverancierspecifieke Supabase-API.

## Veilig migreren

`migrate_to_cloud.py` maakt altijd eerst een gedateerde SQLite-back-up,
controleert de integriteit en schrijft een controlemanifest met SHA-256,
regelaantallen en financiële totalen.

Zonder `--execute` wordt PostgreSQL nooit gewijzigd. Met `--execute` wordt de
volledige import in één transactie uitgevoerd. Daarna worden alle regelaantallen
en financiële controletotalen met SQLite vergeleken.

## Geheimen

De PostgreSQL-URL staat alleen in `GEERTOS_DATABASE_URL` via Streamlit Secrets
of een lokale omgevingsvariabele. Een echte URL wordt nooit in GitHub gezet.

## Nog niet in Sprint 8A

- Geen synchronisatielogica uit Sprint 8B.
- Geen verplaatsing van berekeningen uit Sprint 8C.
- Geen nieuwe dashboardfuncties.

