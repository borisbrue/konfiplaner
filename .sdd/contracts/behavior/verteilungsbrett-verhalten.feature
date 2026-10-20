# language: de
Funktionalität: Verteilungsbrett mit Drag and Drop (SPEC-0013, CON-0018)
  Als Planer:in
  möchte ich Lehrkräfte per Ziehen zwischen Konferenzen verschieben
  um die Personen bestmöglich zu verteilen

  Hintergrund:
    Angenommen ein berechneter Plan mit mehreren Konferenzen im selben Slot

  Szenario: Brett zeigt Spalten und Karten
    Wenn ich den Reiter "Verteilung" öffne
    Dann gibt es eine Spalte je Konferenz und die Spalte "Ohne Zuteilung"
    Und jede Karte zeigt Namen und weitere Konferenzen des Sets

  Szenario: Kopf zeigt Zahlen
    Wenn ich eine Spalte ansehe
    Dann zeigt der Kopf Teilnehmerzahl, Mindestanzahl und Zielgröße

  Szenario: Unter Mindestanzahl ist sichtbar
    Angenommen eine Konferenz hat weniger Teilnehmende als ihre Mindestanzahl
    Dann steht im Kopf "unter Mindestanzahl"

  Szenario: Karte in eine andere Konferenz ziehen
    Angenommen eine Lehrkraft mit zwei Konferenzen im Set
    Wenn ich ihre Karte in die andere Spalte ziehe
    Dann nimmt sie dort teil und nicht mehr in der alten Konferenz
    Und alle Tabellen zeigen die neue Verteilung

  Szenario: Verschieben speichert eine feste Zuweisung
    Wenn ich eine Lehrkraft verschiebe und danach alles neu plane
    Dann bleibt sie in der neuen Konferenz

  Szenario: Ablegen außerhalb des Sets ist eine Ausnahme
    Wenn ich eine Karte in eine Konferenz außerhalb ihres Sets ziehe
    Dann nimmt die Lehrkraft dort teil
    Und die Konferenz steht am Ende ihres Sets
    Und eine Warnung nennt die Ausnahme

  Szenario: Rückmeldung beim Ziehen
    Wenn ich eine Karte über eine Spalte ziehe, die im Set der Lehrkraft liegt
    Dann zeigt die Spalte einen Akzentrahmen
    Und über einer Spalte außerhalb des Sets einen gestrichelten Rahmen mit dem Hinweis "Ausnahme"

  Szenario: Vorsitz ist gesperrt
    Wenn ich den Vorsitz einer Konferenz verschieben will
    Dann ist seine Karte nicht ziehbar
    Und die Meldung nennt den Weg über den Dialog "Bearbeiten"

  Szenario: Prüfhinweise nach dem Verschieben
    Angenommen eine Konferenz hat die Mindestanzahl 3 und genau 3 Teilnehmende
    Wenn ich eine Lehrkraft daraus verschiebe
    Dann steht der Hinweis zur Mindestanzahl im Kopf des Bretts, im Plan und im Export

  Szenario: Überschneidung wird verhindert
    Wenn ich eine Lehrkraft verschiebe, die in einer anderen Konferenz im selben Zeitfenster saß
    Dann nimmt sie nur noch an der neuen teil

  Szenario: Getrennte Konferenzen bleiben
    Angenommen eine Lehrkraft nimmt an zwei zeitlich getrennten Konferenzen teil
    Wenn ich sie aus einer in eine dritte verschiebe
    Dann bleibt ihre Teilnahme an der anderen erhalten

  Szenario: Rückgängig
    Wenn ich eine Verschiebung rückgängig mache
    Dann sind Plan, Set und Zuweisung der Lehrkraft wie vorher

  Szenario: Mehrere Rückgängig
    Wenn ich zwei Verschiebungen mache und zweimal rückgängig
    Dann ist der Ausgangsplan wiederhergestellt

  Szenario: Tastaturbedienung
    Wenn ich eine Karte wähle und Enter drücke
    Dann kann ich im Menü "Verschieben nach" die Ziel-Konferenz wählen
    Und Konferenzen im Set und Ausnahmen sind im Menü gekennzeichnet

  Szenario: Ohne Zuteilung
    Angenommen eine Lehrkraft nimmt an keiner Konferenz teil
    Dann steht ihre Karte in "Ohne Zuteilung" und lässt sich in jede Konferenz ziehen

  Szenario: Zurücksetzen löst die Zuweisung
    Angenommen ich habe eine Lehrkraft verschoben
    Wenn ich sie zurücksetze
    Dann gilt wieder ihr ursprüngliches Set und der Plan bleibt bis zur Neuplanung

  Szenario: Plan und Export stimmen überein
    Wenn ich verschoben habe und exportiere
    Dann zeigt der Export dieselbe Verteilung wie das Brett

  Szenario: Kleine Bildschirme
    Wenn das Fenster 1024 mal 600 Pixel groß ist
    Dann scrollt das Brett waagerecht und bleibt bedienbar
