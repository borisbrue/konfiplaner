# language: de
Funktionalität: Konferenzauswahl (SPEC-0009, CON-0014)
  Als Planer:in
  möchte ich aus allen Konferenzen eine Auswahl treffen
  um nur die stattfindenden Konferenzen zu planen

  Hintergrund:
    Angenommen eine geladene Lehrerliste mit Konferenzterminen

  Szenario: Standard ist alles ausgewählt
    Wenn ich die Konferenzen ansehe
    Dann sind alle ausgewählt

  Szenario: Abgewählte Konferenz kommt im Plan nicht vor
    Angenommen ich wähle "Sport" ab
    Wenn ich plane
    Dann gibt es keinen Termin "Sport" und niemand nimmt an "Sport" teil
    Und kein Verstoß nennt "Sport"

  Szenario: Rest der eigenen Konferenzen rückt nach
    Angenommen eine Lehrkraft mit Fachkonferenz I "Deutsch" und II "Sport", beide gleichzeitig
    Wenn ich "Deutsch" abwähle und plane
    Dann nimmt sie an "Sport" teil, weil "Sport" jetzt ihre erste Konferenz ist
    Und es gibt keinen Verstoß für sie

  Szenario: Abgewählte Konferenz hat keinen Vorsitz im Modell
    Angenommen "Anna" ist Vorsitz von "Deutsch"
    Wenn ich "Deutsch" abwähle
    Dann hat "Deutsch" im Modell keinen Vorsitz
    Und nach erneutem Auswählen ist "Anna" wieder Vorsitz

  Szenario: Lehrkraft ohne verbleibende Konferenz
    Angenommen eine Lehrkraft mit nur der Konferenz "Sport"
    Wenn ich "Sport" abwähle
    Dann steht sie in der Liste "Neu zuordnen" und nicht in "Ohne Konferenz"
    Und sie nimmt an keinem Termin teil

  Szenario: Lehrkraft ohne Konferenz in der Datei
    Angenommen eine Lehrkraft ohne Konferenz in der Datei
    Wenn ich eine Konferenz abwähle
    Dann bleibt sie in der Liste "Ohne Konferenz" und nicht in "Neu zuordnen"

  Szenario: Hinweis im Plan und Export
    Angenommen eine Lehrkraft steht in "Neu zuordnen"
    Wenn ich plane und exportiere
    Dann steht die Warnung "hat durch die Auswahl keine Konferenz" im Blatt "Hinweise"

  Szenario: Nichts ausgewählt
    Angenommen ich wähle alle Konferenzen ab
    Dann ist "Planen" nicht möglich

  Szenario: Änderung verwirft den Plan
    Angenommen es gibt einen Plan
    Wenn ich die Auswahl ändere
    Dann gibt es keinen Plan mehr

  Szenario: Auswahl wird gemerkt
    Angenommen ich habe "Sport" abgewählt und die App neu gestartet
    Wenn ich dieselbe Datei lade
    Dann ist "Sport" weiter abgewählt

  Szenario: Unbekannte gespeicherte Abwahl
    Angenommen die gespeicherte Abwahl nennt eine Konferenz, die es nicht gibt
    Wenn ich die Datei lade
    Dann wird sie ignoriert

  Szenario: GUI-Seite Konferenzen
    Angenommen eine geladene Datei
    Dann zeigt die Seite "Konferenzen" Häkchen, Mitgliederzahl, Vorsitz und Termine je Konferenz
    Und "Alle" und "Keine" setzen alle Häkchen
    Und die Listen "Neu zuordnen" und "Ohne Konferenz" zeigen die betroffenen Personen
