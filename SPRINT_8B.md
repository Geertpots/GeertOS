# Sprint 8B — synchronisatie

GeertOS gebruikt één centrale PostgreSQL-database voor laptop en iPhone.
Wijzigingen worden rechtstreeks in die database opgeslagen; er bestaat geen
aparte synchronisatiekopie en er is geen handmatige synchronisatieknop.

## Conflictbeveiliging

Voor iedere bewerkbare tabel bewaart `sync_state` een versienummer. Een scherm
onthoudt de versie die het heeft geladen. Als een ander apparaat dezelfde tabel
eerder opslaat, weigert GeertOS een verouderde opslagpoging en laadt het
automatisch de nieuwste cloudgegevens. Zo kan een oud laptopscherm een nieuwere
iPhone-wijziging niet ongemerkt overschrijven.

## Reikwijdte

- Geen nieuwe dashboardpagina's.
- Geen dubbele database.
- Geen leveranciersspecifieke Supabase-code.
- Geen onderdelen van Sprint 8C; berekeningen zijn niet verplaatst.
