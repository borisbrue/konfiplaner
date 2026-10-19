# language: de
Funktionalität: Manuelle Zuordnung und Teilneuplanung (SPEC-0010, CON-0015)
  Als Planer:in
  möchte ich Lehrkräfte selbst zuordnen und nur sie neu verplanen
  damit der übrige Plan unverändert bleibt

  Hintergrund:
    Angenommen eine Lehrerliste mit Konferenzterminen und ein vorhandener Plan

  Szenario: Konferenzen und Rangfolge ersetzen
    Wenn ich für "Anna" die Konferenzen "Sport, Deutsch" festlege
    Dann hat sie "Sport" als erste und "Deutsch" als zweite Konferenz
    Und sie ist als "neu zu verplanen" markiert

  Szenario: Änderung gilt vor der Auswahl
    Angenommen ich habe "Sport" abgewählt
    Wenn ich für "Anna" die Konferenzen "Sport, Deutsch" festlege
    Dann nimmt sie im Modell nur an "Deutsch" teil

  Szenario: Sammeländerung hinzufügen
    Wenn ich für "Anna" und "Ben" die Konferenz "Kunst" hinzufüge
    Dann haben beide "Kunst" als letzte Konferenz

  Szenario: Sammeländerung an einer Position
    Wenn ich für "Anna" und "Ben" die Konferenz "Kunst" an Position 1 hinzufüge
    Dann ist "Kunst" ihre erste Konferenz

  Szenario: Sammeländerung entfernen
    Wenn ich für "Anna" und "Ben" die Konferenz "Sport" entferne
    Dann haben beide "Sport" nicht mehr

  Szenario: Unbekannte Konferenz
    Wenn ich für "Anna" die Konferenz "Latein" festlege
    Dann erhalte ich einen Fehler

  Szenario: Vorsitz wechseln
    Wenn ich den Vorsitz von "Deutsch" von "Anna" auf "Ben" ändere
    Dann ist "Ben" Vorsitz von "Deutsch"
    Und "Anna" und "Ben" sind markiert

  Szenario: Vorsitz auf unbekannte Person
    Wenn ich den Vorsitz von "Deutsch" auf "Niemand" ändere
    Dann erhalte ich einen Fehler

  Szenario: Termin sperren
    Wenn ich für "Anna" den Termin von "Sport" sperre und plane
    Dann nimmt "Anna" an diesem Termin nicht teil

  Szenario: Teilnahme fest vorgeben
    Angenommen "Anna" hat zwei gleichzeitige Konferenzen, die zweite ist ihr Rang 2
    Wenn ich ihre Teilnahme an der zweiten fest vorgebe und plane
    Dann nimmt sie an der zweiten teil

  Szenario: Feste Teilnahme an zwei gleichzeitigen Terminen
    Wenn ich für "Anna" zwei gleichzeitige Termine fest vorgebe
    Dann gibt es keinen Plan und die Begründung nennt beide Konferenzen

  Szenario: Nur markierte Lehrkräfte ändern sich
    Angenommen ich habe "Anna" eine andere Konferenz zugeordnet
    Wenn ich die markierten Lehrkräfte neu verplane
    Dann ist die Teilnahme aller anderen Lehrkräfte unverändert
    Und die Markierung ist gelöscht

  Szenario: Teilneuplanung ohne Plan
    Angenommen es gibt noch keinen Plan
    Wenn ich die markierten Lehrkräfte neu verplane
    Dann wird vollständig geplant

  Szenario: Teilneuplanung unlösbar
    Angenommen die Änderung unterschreitet die Mindestanzahl einer Konferenz
    Wenn ich die markierten Lehrkräfte neu verplane
    Dann erhalte ich "kein Plan" mit Begründung
    Und der bisherige Plan und die Markierung bleiben

  Szenario: Vorsitzwechsel bei Teilneuplanung
    Angenommen ich habe den Vorsitz von "Deutsch" auf "Ben" geändert
    Wenn ich die markierten Lehrkräfte neu verplane
    Dann ist "Ben" in jedem Termin von "Deutsch"

  Szenario: Alles neu planen löscht Markierungen
    Angenommen "Anna" ist markiert
    Wenn ich alles neu plane
    Dann ist niemand mehr markiert

  Szenario: Zurücksetzen
    Angenommen ich habe "Anna" Änderungen gegeben
    Wenn ich "Anna" zurücksetze
    Dann gelten wieder ihre ursprünglichen Konferenzen und sie ist nicht markiert

  Szenario: Änderungen überstehen Neuladen
    Angenommen ich habe "Anna" geändert und die App neu gestartet
    Wenn ich dieselbe Datei lade
    Dann gelten die Änderungen weiter

  Szenario: Änderungen gelten nicht für eine andere Datei
    Angenommen ich habe "Anna" geändert
    Wenn ich eine andere Datei lade
    Dann werden die Änderungen nicht angewandt

  Szenario: Konferenzen ohne Festtermine bei Teilneuplanung
    Angenommen eine Konferenz ohne Festtermine
    Wenn ich die markierten Lehrkräfte neu verplane
    Dann behält die Konferenz ihre bisherigen Startslots

  Szenario: GUI Lehrkräfte
    Angenommen eine geladene Lehrerliste
    Dann zeigt die Seite "Lehrkräfte" Konferenzen, Vorsitz, Teilnahme und Status je Lehrkraft
    Und der Dialog "Bearbeiten" und die "Sammeländerung" ändern die Zuordnung
    Und "Markierte neu verplanen" startet die Teilneuplanung
