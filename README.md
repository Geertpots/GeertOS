# Project Vrijheid

Een persoonlijke financiële desktop-app voor vermogen, beleggingen, pensioen,
lijfrente, uitgaven en de verkoop van een bedrijf.

## Starten op Windows

1. Installeer Python 3.11 of nieuwer via https://www.python.org/downloads/
2. Pak deze map uit.
3. Open Opdrachtprompt in deze map.
4. Installeer de onderdelen:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Dubbelklik daarna op `start.bat`.

De app opent automatisch in je browser en werkt als een lokale desktop-app.
Je financiële gegevens blijven op je eigen computer in `project_vrijheid.db`.

## Opbouw

- `app.py` — navigatie en schermen
- `database.py` — SQLite-opslag en standaardgegevens
- `calculations.py` — alle financiële berekeningen
- `styles.py` — lichte en donkere vormgeving

## Let op

De berekeningen zijn bedoeld voor planning en scenariovergelijking. Belastingen,
lijfrentetarieven, AOW en pensioen zijn vereenvoudigde aannames en geen fiscaal
of financieel advies.


## Sprint 6
Familie en Opa-fonds zijn toegevoegd als werkende, zichtbare onderdelen. Stortingen en wijzigingen worden lokaal opgeslagen in SQLite en verschijnen direct op het Dashboard.
