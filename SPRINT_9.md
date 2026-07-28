# Sprint 9 – Persoonlijke financiële waarheid

## Doel

GeertOS maakt voortaan zichtbaar welke cijfers werkelijk zijn, welke waarden
planningsaannames zijn en welke gegevens nog door accountant, fiscalist, bank of
pensioenuitvoerder moeten worden bevestigd.

## Gerealiseerd

- centrale pagina **Persoonlijke waarheid**;
- controlelijst van bedragen, bronnen en aannames;
- exacte AOW-, pensioen- en lijfrentedatums in de inkomensprojectie;
- afzonderlijke vermogensweergave voor privé en BV;
- plan-versus-werkelijkheidregistratie per maand;
- fiscale verkoopuitsplitsing voor privé/eenmanszaak of BV;
- afzonderlijke weergave van boekwinst pand, boekwinst voorraad,
  verkoopkosten, belastbare winst, inkomstenbelasting, Vpb, box 2,
  netto privé en vermogen dat in de BV blijft;
- automatische databasekopie vóór de eerste Sprint 9-schemawijziging.

## Belangrijke grens

GeertOS levert een transparant planningsmodel, geen belastingaangifte of
persoonlijk fiscaal advies. Tarieven en fiscale behandeling blijven expliciete
aannames totdat een accountant of fiscalist ze schriftelijk heeft bevestigd.

## Behoud bestaande werking

Oude verkoopberekeningen blijven standaard de bestaande structuur
`Privé/eenmanszaak` gebruiken. Bestaande balansregels worden bij migratie
veilig als `Privé` aangemerkt en kunnen daarna handmatig aan `BV` worden
toegewezen.
