# language: de
Funktionalität: Restriktionen (SPEC-0003, CON-0006)
  Als Planer:in
  möchte ich Planungsregeln anpassen und erweitern
  um den Plan an wechselnde Anforderungen anzupassen

  Szenario: Neue Regel registrieren
    Angenommen eine Restriktion "NichtZusammen" ist registriert
    Wenn ich plane mit den Parametern Person A und Person B
    Dann sind A und B in keinem gemeinsamen Termin

  Szenario: Grundregel deaktivieren
    Angenommen die Regel "keine_ueberschneidung" ist auf "aus" gestellt
    Wenn ich plane
    Dann wird sie nicht angewendet

  Szenario: Grundregel von hart auf weich
    Angenommen die Regel "schwerpunkte" ist weich mit Gewicht 5
    Wenn kein Plan alle Schwerpunkte erfüllt
    Dann erhalte ich einen Plan mit gemeldeten Verstößen statt "kein Plan"

  Szenario: Unbekannte Regel
    Angenommen die Konfiguration nennt eine nicht registrierte Regel
    Wenn ich plane
    Dann erhalte ich vor dem Solverlauf einen Fehler

  Szenario: Doppelter Regelname
    Angenommen zwei Restriktionen mit demselben Namen
    Wenn ich sie registriere
    Dann erhalte ich einen Fehler

  Szenario: Weiche Regel ohne Gewicht
    Angenommen eine weiche Regel ohne Gewicht
    Wenn ich plane
    Dann gilt das Gewicht 1
