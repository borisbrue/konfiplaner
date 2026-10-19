# language: de
Funktionalität: Excel-Export (SPEC-0004, CON-0009)
  Als Planer:in
  möchte ich den Plan als Excel speichern
  um ihn zu verteilen

  Szenario: Plan exportieren
    Angenommen ein fertiger Plan
    Wenn ich nach "plan.xlsx" exportiere
    Dann enthält die Datei die Blätter "Termine", "Personen", "Themen" und "Hinweise"
    Und jede Person erscheint mit allen ihren Terminen in zeitlicher Reihenfolge

  Szenario: Plan nicht optimal
    Angenommen ein Plan mit Kennzeichen "nicht optimal"
    Wenn ich exportiere
    Dann steht dies im Blatt "Hinweise"

  Szenario: Zieldatei existiert
    Angenommen die Zieldatei existiert
    Wenn ich ohne Bestätigung exportiere
    Dann wird sie nicht überschrieben

  Szenario: Zieldatei gesperrt
    Angenommen die Zieldatei ist von einem anderen Programm gesperrt
    Wenn ich exportiere
    Dann erhalte ich eine klare Fehlermeldung
