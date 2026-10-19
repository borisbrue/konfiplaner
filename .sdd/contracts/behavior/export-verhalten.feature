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

  Szenario: Termine mit Zeit und Teilnehmenden
    Angenommen ein Plan mit einem Termin "Taufe" von Slot 1 bis 2 mit den Teilnehmenden Anna und Ben
    Wenn ich exportiere
    Dann zeigt das Blatt "Termine" Tag, Start- und Endzeit des Termins, die Teilnehmerzahl 2 und beide Namen

  Szenario: Themenauslastung
    Angenommen ein Thema mit Mindestanzahl 3 und einem Termin mit 2 Teilnehmenden
    Wenn ich exportiere
    Dann steht im Blatt "Themen" für dieses Thema "Erfüllt" = "nein"

  Szenario: Kein Plan
    Angenommen ein Ergebnis mit Status "kein_plan" und einer Begründung
    Wenn ich exportiere
    Dann ist das Blatt "Termine" leer
    Und die Begründung steht im Blatt "Hinweise"

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
