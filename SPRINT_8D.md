# Sprint 8D – stabiliteit en beveiliging

Sprint 8D versterkt de bestaande cockpit zonder nieuwe financiële functies of
leveranciers toe te voegen.

## Uitgevoerd

- Een cloudback-up wordt na aanmaak inhoudelijk gecontroleerd op alle negen
  tabellen en de aantallen regels.
- De gebruiker kan een gecontroleerde back-up vanuit GeertOS downloaden.
- Alle bewerkbare tabellen verwijderen volledig lege regels en controleren
  verplichte velden, getallen en datums vóór de bestaande gegevens worden
  vervangen.
- Een databasefout toont een begrijpelijke melding en wijzigt geen gegevens.
- De toegangscode ondersteunt voortaan een PBKDF2-hash, vijf-pogingenlimiet,
  tijdelijke blokkade en automatische sessievergrendeling na dertig minuten.
- De bestaande mobiele CSS-regels zijn met een regressietest vastgelegd.

## Toegepaste CTO-stopregel

### Persoonlijke gebruikersaccounts

Supabase Auth met Row Level Security is nu niet toegevoegd. GeertOS heeft één
eigenaar. De invoering zou alle financiële tabellen moeten koppelen aan
gebruikers-id's en vergroot migratie- en onderhoudsrisico zonder huidig
functioneel voordeel. De versterkte toegangscode past beter bij deze fase.

Herbeoordelen zodra meerdere zelfstandige gebruikers ieder afgeschermde
gegevens nodig hebben.

### Volautomatische externe dagelijkse back-up

Streamlit Community Cloud heeft geen duurzame lokale schijf en Supabase Free
biedt geen professionele, onafhankelijk bewaarde dagelijkse herstelketen.
Een “automatische” export binnen dezelfde tijdelijke omgeving zou
schijnveiligheid geven. Daarom is gekozen voor een volledige, gevalideerde
downloadbare back-up zonder extra kosten of vendor lock-in.

Herbeoordelen zodra betaalde hosting of een onafhankelijke back-upbestemming
wordt gekozen. Tot die tijd adviseert GeertOS een periodieke handmatige export.
