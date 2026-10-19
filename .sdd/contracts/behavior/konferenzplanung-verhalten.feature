# language: de
Funktionalität: Konferenzplanung mit festen Zeitslots (SPEC-0008, CON-0013)
  Als Planer:in
  möchte ich Konferenzen mit festen Terminen planen
  um zu sehen, wer wo teilnimmt und wo Termine kollidieren

  Hintergrund:
    Angenommen eine Lehrerliste und ein Blatt "Konferenzen" mit Konferenz, Tag, Start und Ende

  Szenario: Konferenztermine ersetzen das Zeitraster
    Angenommen jede Konferenz hat eine Zeile im Blatt "Konferenzen"
    Wenn ich importiere
    Dann gibt es Zeitslots und ich kann ohne Zeitraster-Formular planen

  Szenario: Konferenz ohne Termin
    Angenommen die Konferenz "Sport" hat keine Zeile im Blatt "Konferenzen"
    Wenn ich importiere
    Dann ist das ein Fehler mit der Konferenz "Sport"

  Szenario: Konferenzname wird normalisiert
    Angenommen das Blatt "Konferenzen" nennt "Mathe" und die Konferenz heißt "Mathematik"
    Wenn ich importiere
    Dann ist "Mathe" ein Vorschlag, der wie in der Lehrerliste bestätigt wird

  Szenario: Ungültige Zeit
    Angenommen eine Zeile mit Ende vor dem Start
    Wenn ich importiere
    Dann ist das ein Fehler mit Blatt, Zeile und Spalte "Ende"

  Szenario: Mehrere Termine derselben Konferenz überschneiden sich
    Angenommen zwei Zeilen der Konferenz "Deutsch" mit überlappenden Zeiten
    Wenn ich importiere
    Dann ist das ein Fehler

  Szenario: Widersprüchliche Konferenzwerte
    Angenommen zwei Zeilen der Konferenz "Deutsch" mit unterschiedlicher Mindestanzahl
    Wenn ich importiere
    Dann ist das ein Fehler in Blatt "Konferenzen" und Spalte "Mindestanzahl"

  Szenario: Gleichzeitige Konferenzen, Rangfolge entscheidet
    Angenommen eine Lehrkraft mit Fachkonferenz I "Deutsch" und II "Sport" im selben Zeitfenster
    Wenn ich plane
    Dann nimmt sie an "Deutsch" teil
    Und der Plan nennt die entgangene Teilnahme an "Sport" als Verstoß

  Szenario: Rangfolge bei drei Konferenzen
    Angenommen eine Lehrkraft mit drei gleichzeitigen Konferenzen I, II und III
    Wenn ich plane
    Dann nimmt sie an Konferenz I teil

  Szenario: Teilüberlappung zählt
    Angenommen "Deutsch" von 14:00 bis 15:30 und "Sport" von 15:00 bis 16:00 am selben Tag
    Wenn ich plane
    Dann kann eine Lehrkraft mit beiden nicht an beiden teilnehmen

  Szenario: Getrennte Konferenzen ohne Konflikt
    Angenommen "Deutsch" von 14:00 bis 15:00 und "Sport" von 15:00 bis 16:00
    Wenn ich plane
    Dann nimmt die Lehrkraft an beiden teil und es gibt keinen Verstoß

  Szenario: Konferenz mit zwei Terminen
    Angenommen "Deutsch" hat zwei feste Termine und einen Vorsitz
    Wenn ich plane
    Dann nimmt der Vorsitz an beiden teil und jede andere Lehrkraft an höchstens einem

  Szenario: Solver verschiebt feste Termine nicht
    Angenommen eine Konferenz mit festem Termin
    Wenn ich plane
    Dann liegt der Termin genau im Zeitfenster des Blatts

  Szenario: Vorsitz in zwei gleichzeitigen Konferenzen
    Angenommen eine Person ist Vorsitz zweier Konferenzen im selben Zeitfenster
    Wenn ich plane
    Dann ist der Status "kein_plan" und die Begründung nennt beide Konferenzen

  Szenario: Standardregel für Lehrerlisten mit Terminen
    Angenommen die Datei enthält Konferenztermine und ich habe "schwerpunkte" nicht selbst gesetzt
    Wenn ich plane
    Dann ist "schwerpunkte" weich und es gibt trotz Überschneidungen einen Plan

  Szenario: Selbst gesetzte Regel bleibt
    Angenommen ich habe "schwerpunkte" selbst auf "hart" gesetzt
    Wenn ich eine Datei mit Konferenztermine lade
    Dann bleibt "schwerpunkte" hart

  Szenario: Unterkonferenz vor Hauptkonferenz
    Angenommen "Sowi" hat die Hauptkonferenz "GL" und beginnt vor dem Ende von "GL"
    Wenn ich importiere
    Dann gibt es eine Warnung und keinen Fehler

  Szenario: Konflikte im Ergebnis und Export
    Angenommen ein Plan mit entgangener Teilnahme
    Wenn ich das Ergebnis ansehe und exportiere
    Dann steht der Verstoß mit Person und Konferenz im Reiter "Hinweise" und im Blatt "Hinweise"

  Szenario: GUI zeigt Termine je Konferenz
    Angenommen eine geladene Datei mit Konferenztermine
    Dann zeigt die Seite "Daten" den Reiter "Termine" und das Zeitraster-Formular ist abgeschaltet
