# language: de
Funktionalität: Lehrerlisten-Import und Normalisierung (SPEC-0007, CON-0012)
  Als Planer:in
  möchte ich die Lehrerliste mit Fachkonferenzen laden und uneinheitliche Namen einmal zuordnen
  um ohne Umbau der Liste zu planen

  Hintergrund:
    Angenommen eine Lehrerliste mit den Spalten Nachname, Vorname, Fächer, Fachkonferenz I, Fachkonferenz II, Fachkonferenz III und Vorsitzende

  Szenario: Format wird erkannt und Namen werden zusammengesetzt
    Angenommen die Zeile "Meier", "Anna" mit den Konferenzen "Deutsch" und "Englisch"
    Wenn ich importiere
    Dann gibt es die Person "Anna Meier" mit den Konferenzen Deutsch, Englisch in dieser Reihenfolge

  Szenario: Spaltenüberschriften sind tolerant
    Angenommen die Überschrift der dritten Konferenzspalte lautet "ggfs. FK III (Absprache mit der Leitung)"
    Wenn ich importiere
    Dann wird die Spalte als Fachkonferenz III erkannt

  Szenario: Exakte Namen sind sicher
    Angenommen die Konferenzen "deutsch" und "Deutsch " und die Vorsitz-Konferenz "Deutsch"
    Wenn ich importiere
    Dann gibt es keinen Fehler und beide Zellen bedeuten die Konferenz "Deutsch"

  Szenario: Abweichende Schreibweise ist nur ein Vorschlag
    Angenommen eine Zelle "Mathe" und die Vorsitz-Konferenz "Mathematik"
    Wenn ich importiere
    Dann enthält die Fehlerliste Blatt, Zeile und Spalte der Zelle mit dem Vorschlag "Mathematik"
    Und es wird kein Modell geliefert

  Szenario: Bestätigen löst den Fehler für alle Vorkommen
    Angenommen "Mathe" kommt in drei Zellen vor
    Wenn ich "Mathe" als "Mathematik" bestätige und neu importiere
    Dann gibt es keinen Fehler mehr

  Szenario: Zusammengesetzte Zelle muss einzeln bestätigt werden
    Angenommen eine Zelle "GL/Sowi" und die Konferenzen GL und Sowi
    Wenn ich importiere
    Dann ist die Zelle ein Fehler mit dem Vorschlag "GL, Sowi"
    Und nach dem Bestätigen ist die Person Mitglied in GL und Sowi

  Szenario: Schreibweise des Schlüssels
    Angenommen die Zellen "GL/Sowi", "GL / Sowi" und "gl/ sowi"
    Wenn ich eine Zuordnung bestätige
    Dann gilt sie für alle drei

  Szenario: Unbekannter Wert ohne Vorschlag
    Angenommen eine Zelle "TC" ohne passende Konferenz
    Wenn ich importiere
    Dann ist die Zelle ein Fehler ohne Vorschlag
    Und ich kann ihr eine Konferenz zuordnen

  Szenario: Person ohne Konferenz
    Angenommen eine Zeile ohne Konferenzen
    Wenn ich importiere
    Dann enthält das Ergebnis eine Warnung und die Person steht in der Liste "ohne Konferenz"
    Und das Planungsmodell enthält sie ohne Termine

  Szenario: Person mit einer Konferenz
    Angenommen eine Zeile mit nur "Fachkonferenz I"
    Wenn ich importiere
    Dann hat die Person genau diese eine Konferenz

  Szenario: Dieselbe Konferenz in zwei Spalten
    Angenommen eine Zeile mit "Deutsch" in Fachkonferenz I und Fachkonferenz II
    Wenn ich importiere
    Dann steht "Deutsch" einmal in den Konferenzen der Person

  Szenario: Vorsitz aus der Spalte Vorsitzende
    Angenommen die Person "Anna Meier" hat in "Vorsitzende" den Wert "Deutsch"
    Wenn ich importiere
    Dann ist "Anna Meier" Vorsitz der Konferenz "Deutsch"

  Szenario: Vorsitz ohne Mitgliedschaft
    Angenommen die Person leitet "Geschichte", hat Geschichte aber nicht als Konferenz
    Wenn ich importiere
    Dann ist sie trotzdem Vorsitz von "Geschichte"

  Szenario: Zwei Vorsitzende derselben Konferenz
    Angenommen zwei Personen mit dem Wert "Deutsch" in "Vorsitzende"
    Wenn ich importiere
    Dann ist das ein Fehler

  Szenario: Doppelter Name
    Angenommen zwei Zeilen mit demselben Vor- und Nachnamen
    Wenn ich importiere
    Dann gibt es eine Warnung und die erste Zeile gilt

  Szenario: Bestätigte Zuordnungen werden gemerkt
    Angenommen ich habe "Mathe" als "Mathematik" bestätigt und die App neu gestartet
    Wenn ich dieselbe Liste lade
    Dann ist "Mathe" ohne erneute Bestätigung zugeordnet

  Szenario: Themenwerte bleiben beim Neuladen
    Angenommen ich habe die Mindestanzahl einer Konferenz geändert
    Wenn ich die Datei neu lade
    Dann gilt weiter die geänderte Mindestanzahl

  Szenario: GUI zeigt Normalisierung und Personen ohne Konferenz
    Angenommen eine geladene Lehrerliste
    Dann zeigt die Seite "Daten" den Reiter "Normalisierung" mit Rohwert, Vorkommen, Zuordnung und Status
    Und den Reiter "Ohne Konferenz" mit den Namen
    Und "Alle Vorschläge übernehmen" bestätigt alle Vorschläge
