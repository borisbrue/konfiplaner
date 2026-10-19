# language: de
Funktionalität: Planung (SPEC-0002, CON-0004)
  Als Planer:in
  möchte ich einen Terminplan berechnen lassen
  um Personen thematisch passend zu Terminen zusammenzustellen

  Szenario: Einfacher Plan
    Angenommen 3 Themen, 12 Personen mit je 2 Themen und 6 Zeitslots
    Wenn ich plane
    Dann findet jedes Thema statt
    Und jede Person ist in den Terminen ihrer beiden Themen

  Szenario: Nur ein Termin je Thema
    Angenommen ein Thema mit Mindestanzahl 3 und genau 3 interessierten Personen
    Wenn ich plane
    Dann gibt es genau einen Termin dieses Themas mit allen 3 Personen

  Szenario: Mindestanzahl nicht erreichbar
    Angenommen ein Thema mit Mindestanzahl 5 und nur 3 interessierten Personen
    Wenn ich plane
    Dann erhalte ich "kein Plan" mit Begründung zu diesem Thema

  Szenario: Kein Thema entfällt
    Angenommen ein Engpass, der nicht alle Themen vollständig besetzen lässt
    Wenn ich plane
    Dann findet trotzdem jedes Thema statt

  Szenario: Wichtigkeit bei Slot-Konflikt
    Angenommen ein wichtiges und ein unwichtiges Thema mit gemeinsamen Personen und nur einem gemeinsamen Slot
    Wenn ich plane
    Dann erhält das wichtigere Thema den Slot
    Und das unwichtigere Thema weicht auf einen anderen Slot aus

  Szenario: Keine Überschneidung
    Angenommen eine Person mit zwei Themen
    Wenn ich plane
    Dann überschneiden sich die beiden Termine dieser Person nicht

  Szenario: Dauer
    Angenommen ein Thema mit Dauer 90 Minuten und Slots zu je 45 Minuten
    Wenn ich plane
    Dann belegt der Termin zwei aufeinanderfolgende Slots

  Szenario: Reproduzierbarkeit
    Angenommen dieselbe Eingabe und derselbe Seed
    Wenn ich zweimal plane
    Dann sind beide Pläne identisch

  Szenario: Zeitlimit
    Angenommen ein sehr kleines Zeitlimit
    Wenn ich plane
    Dann erhalte ich die beste bisherige Lösung mit Kennzeichen "nicht optimal"
