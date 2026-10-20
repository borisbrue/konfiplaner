# language: de
Funktionalität: Verteilung der Lehrkräfte auf Konferenzen (SPEC-0012, CON-0017)
  Als Planer:in
  möchte ich, dass sich Lehrkräfte auf ihre Konferenzen verteilen
  statt alle gleichzeitig besuchen zu müssen

  Szenario: Lehrerliste planbar ohne Regeländerung
    Angenommen eine Lehrerliste, in der Lehrkräfte zwei bis drei Konferenzen haben, und ein Zeitslot
    Wenn ich plane
    Dann gibt es einen Plan

  Szenario: Jede Lehrkraft nimmt an genau einer Konferenz teil
    Angenommen zwei Konferenzen im selben Slot und Lehrkräfte mit beiden als Set
    Wenn ich plane
    Dann nimmt jede Lehrkraft an genau einer teil

  Szenario: Konferenzen sind möglichst gleich groß
    Angenommen 10 Lehrkräfte mit den Konferenzen "Deutsch" und "Englisch" in beliebiger Reihenfolge und gleichem Slot
    Wenn ich plane
    Dann haben beide Konferenzen je 5 Teilnehmende

  Szenario: Rangfolge als Vorliebe
    Angenommen eine Lehrkraft mit den Konferenzen "Deutsch" und "Sport", beide Konferenzen gleich stark besetzt
    Wenn ich plane
    Dann nimmt sie an "Deutsch" teil

  Szenario: Ausgleich geht vor Rangfolge
    Angenommen "Deutsch" hat 8 mögliche Mitglieder mit Deutsch als erster Konferenz, "Sport" hat 2 Mitglieder
    Wenn ich plane
    Dann nehmen mehrere Lehrkräfte an ihrer zweiten Konferenz "Sport" teil, damit beide ähnlich groß sind

  Szenario: Vorsitz ist gesetzt
    Angenommen "Anna" ist Vorsitz von "Sport", hat aber Deutsch als erste Konferenz
    Wenn ich plane
    Dann nimmt "Anna" an "Sport" teil

  Szenario: Mindestanzahl wird gesichert
    Angenommen "Sport" hat die Mindestanzahl 3 und nur 4 mögliche Mitglieder
    Wenn ich plane
    Dann hat "Sport" mindestens 3 Teilnehmende

  Szenario: Mindestanzahl nicht erreichbar
    Angenommen "Sport" hat die Mindestanzahl 5 und nur 3 mögliche Mitglieder
    Wenn ich plane
    Dann ist der Status "kein_plan" und die Begründung nennt "mindestanzahl" und "Sport"

  Szenario: Zeitlich getrennte Konferenzen
    Angenommen "Deutsch" und "Sport" liegen zeitlich getrennt und eine Lehrkraft hat beide
    Wenn ich plane
    Dann nimmt sie an beiden teil

  Szenario: Keine Verstoßmeldungen für nicht besuchte Konferenzen
    Angenommen eine Lehrkraft nimmt nur an der ersten ihrer zwei Konferenzen teil
    Wenn ich plane
    Dann gibt es keinen Verstoß, der die zweite Konferenz nennt

  Szenario: Ein Treffen je Konferenz
    Angenommen eine Lehrerliste ohne Festtermine
    Wenn ich plane
    Dann hat jede Konferenz genau einen Termin

  Szenario: Profil gilt nur, solange nichts von Hand gesetzt wurde
    Angenommen ich habe "schwerpunkte" selbst auf "hart" gesetzt
    Wenn ich eine Lehrerliste lade
    Dann bleibt "schwerpunkte" hart und der Tipp erscheint, falls es keinen Plan gibt

  Szenario: Tipp bei Unlösbarkeit
    Angenommen "schwerpunkte" ist hart und die Lehrkräfte haben mehrere Konferenzen im selben Slot
    Wenn ich plane
    Dann nennt die Oberfläche den Tipp, die Regel auf "weich" zu stellen

  Szenario: Feste Zuweisung auf Konferenzebene
    Angenommen "Anna" ist fest "Sport" zugewiesen, ihre erste Konferenz ist aber "Deutsch"
    Wenn ich plane
    Dann nimmt "Anna" an "Sport" teil

  Szenario: Unmögliche feste Zuweisung
    Angenommen "Anna" ist fest einer Konferenz zugewiesen, die nicht zu ihrem Set gehört und nicht ihr Vorsitz ist
    Wenn ich plane
    Dann gibt es keinen Plan und die Begründung nennt "fixierung"

  Szenario: Ausgleich lässt sich abschalten
    Angenommen "ausgleich" steht auf "aus"
    Wenn ich plane
    Dann verteilt die Rangfolge allein die Lehrkräfte

  Szenario: Minimalformat bleibt wie bisher
    Angenommen eine Datei im Minimalformat
    Wenn ich plane
    Dann gelten die bisherigen Regeln
