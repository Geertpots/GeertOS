# Controleerbare financiële cockpit

Deze kwaliteitsfase maakt de uitkomsten van GeertOS beter controleerbaar zonder
nieuwe financiële formules toe te voegen.

## Toegevoegd

- drie complete verkoopscenario's: voorzichtig, verwacht en gunstig;
- een herleidbare brug van bruto verkoop naar netto cash;
- automatische controle op ontbrekende kernbedragen en exacte ingangsdatums;
- waarschuwingen wanneer financiële, fiscale of marktgegevens opnieuw moeten
  worden gecontroleerd;
- controledatums op de pagina Persoonlijke financiële waarheid.

## Centrale bron

Alle scenario-uitkomsten lopen via `FinancialEngine.evaluate`. De
gebruikersinterface presenteert de uitkomsten, maar rekent geen alternatieve
bedragen uit. De kwaliteitscontrole wijzigt nooit zelfstandig financiële data.
