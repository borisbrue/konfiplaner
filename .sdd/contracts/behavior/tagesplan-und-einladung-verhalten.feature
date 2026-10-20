# language: de
Funktionalität: Tagesplan und Einladung

  Szenario: Standardablauf ist vorhanden
    Angenommen es wurde noch kein Tagesplan gespeichert
    Dann enthält der Tagesplan die Blöcke Stehkaffee, Begrüßung, Einstieg, Kaffeepause, Fachkonferenzen, Mittagspause, Gruppenarbeit, Austausch und Ende

  Szenario: Zeiten werden im Dokumentformat ausgegeben
    Angenommen ein Block von 8:30 bis 8:40, ein Block ab 8:00 und ein Block um 15:00
    Dann lauten die Zeiten "8.30 – 8.40 Uhr", "ab 8.00 Uhr" und "15.00 Uhr"

  Szenario: Gewählte Konferenzen stehen im Konferenzblock
    Angenommen die Konferenzen Mathematik, Deutsch und Sport sind ausgewählt
    Und die Konferenz Sport wird abgewählt
    Wenn ich die Einladung exportiere
    Dann steht im Konferenzblock "Mathematik, Deutsch"
    Und "Sport" kommt dort nicht vor

  Szenario: Ein Block mit Ende vor Beginn verhindert den Export
    Angenommen ein Block mit Beginn 10:00 und Ende 9:00
    Wenn ich exportiere
    Dann erscheint eine Fehlermeldung und es wird keine Datei geschrieben

  Szenario: Überlappende Blöcke sind nur eine Warnung
    Angenommen zwei Blöcke 9:00 – 10:00 und 9:30 – 10:30
    Dann meldet die Prüfung eine Warnung
    Und der Export ist trotzdem möglich

  Szenario: Die Einladung enthält Kopf und Ablauftabelle
    Angenommen ein Tagesplan mit Datum 09.11.2026, Titel, Thema und zwei Zielen
    Wenn ich als "Einladung.docx" exportiere
    Dann beginnt das Dokument mit "Montag, 09.11.2026: " und dem Titel
    Und es enthält "THEMA: " mit dem Thema
    Und es enthält die Überschrift "Ablaufplan 09.11.2026"
    Und die Tabelle hat die Spalten "Zeiten", "Inhalt" und "Wer/Wie?"
    Und das Dokument ist im Querformat

  Szenario: Leere Abschnitte entfallen
    Angenommen der Tagesplan hat keine Vorbereitung
    Wenn ich exportiere
    Dann kommt "Vorbereitung" im Dokument nicht vor

  Szenario: Tagesplan bleibt zwischen Sitzungen erhalten
    Angenommen ich ändere den Titel und speichere die Einstellungen
    Wenn die App neu startet
    Dann ist der Titel erhalten

  Szenario: Vorhandene Datei wird nur nach Bestätigung überschrieben
    Angenommen die Zieldatei existiert
    Wenn ich exportiere und das Überschreiben verneine
    Dann bleibt die Datei unverändert

  Szenario: Fehlende Logo-Datei wird übergangen
    Angenommen als Logo ist eine nicht vorhandene Datei eingetragen
    Wenn ich exportiere
    Dann entsteht trotzdem ein gültiges Dokument

  Szenario: Ende gleich Beginn ist ein Fehler
    Angenommen ein Block mit Beginn 10:00 und Ende 10:00
    Dann meldet die Prüfung einen Fehler für diesen Block

  Szenario: Konferenzen stehen in der Reihenfolge der Konferenzliste vor dem eigenen Inhalt
    Angenommen der Konferenzblock hat den eigenen Inhalt "Material sichten"
    Wenn die Konferenzen Mathematik und Deutsch ausgewählt sind
    Dann beginnt der Inhalt mit "Mathematik, Deutsch" gefolgt von "Material sichten"

  Szenario: Ohne ausgewählte Konferenz zeigt der Block nur den eigenen Inhalt
    Angenommen keine Konferenz ist ausgewählt
    Dann enthält der Konferenzblock nur seinen eigenen Inhalt

  Szenario: Ohne Datum entfällt das Datum in Titel und Überschrift
    Angenommen der Tagesplan hat kein Datum
    Dann beginnt die Titelzeile ohne Wochentag und die Überschrift lautet "Ablaufplan"

  Szenario: Blöcke lassen sich hinzufügen, löschen und verschieben
    Angenommen die Seite "Einladung" ist geöffnet
    Wenn ich einen Block hinzufüge, nach oben schiebe und einen anderen lösche
    Dann zeigt die Blockliste die geänderte Reihenfolge

  Szenario: Die Seite ist erst nach dem Laden einer Datei verfügbar
    Angenommen noch keine Datei ist geladen
    Dann ist der Schritt "Einladung" gesperrt

  Szenario: Bestätigtes Überschreiben ersetzt die Datei
    Angenommen die Zieldatei existiert
    Wenn ich exportiere und das Überschreiben bestätige
    Dann enthält die Datei die neue Einladung

  Szenario: Ein vorhandenes Logo steht oben rechts
    Angenommen als Logo ist eine vorhandene PNG-Datei eingetragen
    Wenn ich exportiere
    Dann enthält das Dokument ein Bild
