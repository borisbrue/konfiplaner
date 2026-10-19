# language: de
Funktionalität: Vorsitz pro Thema (SPEC-0006, CON-0011)
  Als Planer:in
  möchte ich für ein Thema einen Vorsitz festlegen
  damit diese Person zwingend im Termin ist

  Hintergrund:
    Angenommen die Grundregeln stehen auf ihren Standardwerten

  Szenario: Vorsitz ist im Termin, auch ohne Schwerpunkt
    Angenommen das Thema "Taufe" hat den Vorsitz "Meier", der das Thema nicht als Schwerpunkt hat
    Wenn ich plane
    Dann ist "Meier" Teilnehmer jedes Termins von "Taufe"

  Szenario: Vorsitz zählt zur Mindestanzahl
    Angenommen das Thema "Taufe" hat Mindestanzahl 3, zwei Personen mit Schwerpunkt "Taufe" und den Vorsitz "Meier"
    Wenn ich plane
    Dann gibt es einen Termin "Taufe" mit 3 Teilnehmenden einschließlich "Meier"

  Szenario: Vorsitz in allen Terminen eines Themas
    Angenommen das Thema "Taufe" braucht wegen getrennter Verfügbarkeiten zwei Termine und hat den Vorsitz "Meier"
    Wenn ich plane
    Dann ist "Meier" in beiden Terminen von "Taufe"

  Szenario: Vorsitz mit Schwerpunkt im selben Thema
    Angenommen "Meier" hat "Taufe" als Schwerpunkt und ist Vorsitz von "Taufe"
    Wenn ich plane
    Dann ist "Meier" einmal in jedem Termin von "Taufe"
    Und der Plan erfüllt die Regel "schwerpunkte"

  Szenario: Keine Überschneidung für den Vorsitz
    Angenommen "Meier" ist Vorsitz von "Taufe" und hat die Schwerpunkte "Abendmahl" und "Gebet"
    Wenn ich plane
    Dann überschneidet sich kein Termin von "Meier" mit einem anderen

  Szenario: Vorsitz nicht verfügbar
    Angenommen der Vorsitz "Meier" ist nur in Slot 0 verfügbar und dort läuft sein anderer Termin
    Wenn ich plane
    Dann ist der Status "kein_plan"
    Und die Begründung nennt die Regel "vorsitz" und das Thema

  Szenario: Vorsitz als weiche Regel
    Angenommen die Regel "vorsitz" ist weich mit Gewicht 5 und der Vorsitz kann nicht in jedem Termin sein
    Wenn ich plane
    Dann erhalte ich einen Plan mit Verstößen der Regel "vorsitz"

  Szenario: Vorsitz ausgeschaltet
    Angenommen die Regel "vorsitz" steht auf "aus"
    Wenn ich plane
    Dann ist der Vorsitz nicht zwingend im Termin

  Szenario: Import mit Spalte Vorsitz
    Angenommen das Blatt "Themen" hat die Spalte "Vorsitz" mit dem Namen "Meier" und "Meier" steht in "Personen"
    Wenn ich importiere
    Dann hat das Thema den Vorsitz "Meier"

  Szenario: Import mit unbekanntem Vorsitz
    Angenommen das Blatt "Themen" nennt den Vorsitz "Unbekannt", der nicht in "Personen" steht
    Wenn ich importiere
    Dann enthält die Fehlerliste Blatt "Themen", Zeile und Spalte "Vorsitz"

  Szenario: Import ohne Spalte Vorsitz
    Angenommen das Blatt "Themen" hat keine Spalte "Vorsitz"
    Wenn ich importiere
    Dann gibt es keinen Fehler und kein Thema hat einen Vorsitz

  Szenario: Export zeigt den Vorsitz
    Angenommen ein Plan mit Vorsitz "Meier" für "Taufe"
    Wenn ich exportiere
    Dann zeigt das Blatt "Termine" in der Spalte "Vorsitz" den Namen "Meier"
    Und das Blatt "Personen" zeigt für "Meier" in "Taufe" die Rolle "Vorsitz"

  Szenario: GUI-Auswahl des Vorsitzes
    Angenommen eine geladene Datei mit Personen
    Wenn ich in der Themen-Tabelle für "Taufe" den Vorsitz "Meier" wähle
    Dann ist der Vorsitz gesetzt und ein unbekannter Name wird abgelehnt
