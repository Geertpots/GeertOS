# Sprint 8C – centrale financiële rekenmotor

Sprint 8C brengt de onderling afhankelijke financiële berekeningen samen in
`financial_engine.py`. Deze module bevat geen Streamlit-code en kent ook geen
specifieke cloudprovider. Daardoor kan dezelfde rekenmotor later worden
gebruikt door een mobiele app, desktopapp, API of AI-assistent.

## Eén consistente momentopname

`FinancialEngine.evaluate()` ontvangt één verzameling instellingen en
datatabellen en levert één `FinancialResult` op met:

- verkoopresultaat en netto cash;
- huidig en verwacht netto vermogen na verkoop;
- ETF- en Bitcoinpositie;
- pensioen en lijfrente;
- netto maandinkomen tot en met het ingestelde eindjaar;
- vermogens- en inkomensprojectie;
- plancontrole en Vrijheidsindex.

Een gewijzigd verkoopscenario wordt als tijdelijke override doorgegeven.
Daardoor rekenen alle afhankelijke uitkomsten met exact dezelfde verkoopprijs,
zonder de opgeslagen basisgegevens onbedoeld te wijzigen.

## Behoud en uitbreidbaarheid

De bestaande functies in `calculations.py` blijven de kleine, afzonderlijk
testbare rekenbouwstenen. `financial_engine.py` orkestreert ze centraal.
Streamlit blijft uitsluitend verantwoordelijk voor invoer en presentatie.
Er zijn geen nieuwe diensten, abonnementen, pagina's of cloudafhankelijkheden
toegevoegd.
