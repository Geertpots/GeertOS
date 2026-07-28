# Sprint 10C – Veilige financiële adviseur

## Opgeleverd

- Een vaste AI-assistentpagina in GeertOS.
- Vragen in gewone Nederlandse taal over:
  - verkoopprijs van POTZ WONEN;
  - extra maandelijkse bestedingen;
  - grote aankopen;
  - een daling van Bitcoin;
  - financiële onafhankelijkheid.
- Antwoorden met kernuitkomst, gevolgen, aannames en verwijzing naar de
  relevante bestaande module.
- Voorbeeldvragen om de assistent eenvoudig te gebruiken.

## Veiligheid

- De assistent heeft uitsluitend lees- en rekenrechten.
- Er worden nooit automatisch gegevens of instellingen gewijzigd.
- Er gaan geen financiële gegevens naar een externe AI-dienst.
- Er is geen betaalde dienst toegevoegd.
- Berekeningen gebruiken `FinancialEngine` en de bestaande centrale
  rekenfuncties.

## Bewuste keuze

Sprint 10C gebruikt eerst een lokale, vaste en testbare advieslaag. Een
extern taalmodel kan later optioneel worden toegevoegd, maar uitsluitend na
een aparte kosten-, privacy- en risicoanalyse en expliciete toestemming.

## Back-up

Voor de wijziging is een volledige back-up gemaakt in:

`work/backups/sprint10C_voor_wijziging_20260728_210017`
