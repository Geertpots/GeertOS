# Sprint 10B – Tijdlijn en scenariovergelijking

## Doel

GeertOS maakt de bestaande financiële planning inzichtelijker zonder een
tweede rekenmodel of nieuwe gegevensbron toe te voegen.

## Opgeleverd

- Interactieve tijdlijn van het eerste planjaar tot en met 2047.
- Jaarselectie met inkomen, doel, ETF-restvermogen, opname, pensioen,
  lijfrente, AOW en tekort of overschot.
- Drie vaste scenario's: voorzichtig, verwacht en optimistisch.
- Vergelijking van verkoopprijs, rendement, inflatie, netto cash,
  vermogen, ETF-restvermogen, Bitcoinwaarde en risico.
- Uitlegbare vrijheidsstatus met afzonderlijke inkomens- en bufferscore.

## Bewuste grenzen

- Scenario's wijzigen of bewaren geen gegevens.
- Bitcoin wordt niet naar toekomstige jaren geprojecteerd zolang daarvoor
  geen expliciete en betrouwbare aanname is vastgelegd.
- Er is geen AI-functionaliteit toegevoegd; die hoort niet bij Sprint 10B.
- Er is geen databasestructuur gewijzigd.
- Alle uitkomsten komen uit `FinancialEngine`.

## Herstel

Voor de wijziging is buiten de repository een volledige back-up gemaakt in:

`work/backups/sprint10B_voor_wijziging_20260728_204736`
