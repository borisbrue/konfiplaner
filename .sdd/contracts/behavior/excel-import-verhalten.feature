# language: de
Funktionalität: Excel-Import (SPEC-0001, CON-0002)
  Als Planer:in
  möchte ich meine Excel-Listen laden
  um nicht alle Daten neu eingeben zu müssen

  Szenario: Gültige Datei
    Angenommen eine Excel-Datei mit dem Blatt "Personen" mit den Spalten Name, Thema 1, Thema 2
    Wenn ich sie importiere
    Dann erhalte ich ein Modell mit allen Personen
    Und die Fehlerliste ist leer

  Szenario: Themenset ohne Blatt "Themen"
    Angenommen eine Datei nur mit dem Blatt "Personen"
    Wenn ich importiere
    Dann ergibt sich das Themenset aus den genannten Themen
    Und die Themen erhalten Standardwerte für Wichtigkeit, Mindestanzahl und Dauer

  Szenario: Unbekanntes Thema bei vorhandenem Blatt "Themen"
    Angenommen eine Person mit Thema "Abendmahl" ohne passende Zeile im Blatt "Themen"
    Wenn ich importiere
    Dann enthält die Fehlerliste Blatt, Zeile und Spalte der Zelle
    Und es wird kein Modell geliefert

  Szenario: Zwei gleiche Themen
    Angenommen eine Person mit identischem Thema 1 und Thema 2
    Wenn ich importiere
    Dann enthält die Fehlerliste einen Fehler für diese Zeile

  Szenario: Mehrere Fehler auf einmal
    Angenommen eine Datei mit drei fehlerhaften Zeilen
    Wenn ich importiere
    Dann enthält die Fehlerliste alle drei Fehler

  Szenario: Doppelte Person
    Angenommen zwei Zeilen mit demselben Namen
    Wenn ich importiere
    Dann enthält die Fehlerliste eine Warnung und keinen Fehler

  Szenariogrundriss: Spaltenüberschriften sind tolerant
    Angenommen die Überschrift lautet "<ueberschrift>"
    Wenn ich importiere
    Dann wird die Spalte als "<spalte>" erkannt

    Beispiele:
      | ueberschrift | spalte  |
      | Thema 1      | thema_1 |
      | thema1       | thema_1 |
      |  THEMA 2     | thema_2 |
      | name         | name    |

  Szenario: Beschädigte Datei
    Angenommen eine Datei, die keine gültige Excel-Datei ist
    Wenn ich importiere
    Dann erhalte ich eine verständliche Fehlermeldung statt eines Absturzes

  Szenario: Verfügbarkeiten
    Angenommen Zeitslots und ein Blatt "Verfügbarkeiten" mit Person, Tag und Start
    Wenn ich importiere
    Dann ist die Person nur in den genannten Slots verfügbar
    Und Personen ohne Zeile sind jederzeit verfügbar
