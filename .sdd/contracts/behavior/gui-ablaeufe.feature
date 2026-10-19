# language: de
Funktionalität: GUI-Ablauf (SPEC-0005, CON-0010)
  Als Planer:in
  möchte ich den gesamten Ablauf in einer Oberfläche erledigen
  um ohne Kommandozeile zu planen

  Szenario: Voller Durchlauf
    Angenommen die App ist gestartet
    Wenn ich eine gültige Excel-Datei lade und "Planen" wähle
    Dann sehe ich den Plan nach Termin und Person
    Und kann ihn als Excel exportieren

  Szenario: Fehlerhafte Datei
    Angenommen ich lade eine Datei mit Fehlern
    Wenn der Import fertig ist
    Dann sehe ich die Fehlerliste tabellarisch
    Und "Planen" ist nicht möglich

  Szenario: Planung abbrechen
    Angenommen eine laufende Planung
    Wenn ich "Abbrechen" wähle
    Dann bleibt die Oberfläche bedienbar
    Und ich erhalte die beste bisherige Lösung

  Szenario: Regel anpassen
    Angenommen die Regelverwaltung ist offen
    Wenn ich eine Grundregel von hart auf weich stelle und ein Gewicht setze
    Dann wird die Einstellung gespeichert und bei der nächsten Planung verwendet

  Szenario: Themenwerte und Zeitslots ergänzen
    Angenommen ich lade eine Datei nur mit dem Blatt "Personen"
    Wenn ich Zeitslots per Formular erzeuge
    Dann ist "Planen" möglich
    Und die Themenwerte sind in der Tabelle bearbeitbar

  Szenario: Planen erst bei fehlerfreien Daten
    Angenommen keine Datei ist geladen
    Dann ist "Planen" nicht möglich

  Szenario: Einstellungen merken
    Angenommen ich habe eine Datei geladen und eine Regel auf "weich" gestellt
    Wenn ich die App neu starte
    Dann sind Dateipfad und Regelkonfiguration wiederhergestellt

  Szenario: Export bestätigen
    Angenommen ein fertiger Plan und eine vorhandene Zieldatei
    Wenn ich exportiere und das Überschreiben nicht bestätige
    Dann bleibt die Zieldatei unverändert
