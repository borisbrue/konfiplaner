# language: de
Funktionalität: Update-Hinweis

  Szenariogrundriss: Versionen werden numerisch verglichen
    Angenommen die App hat die Version "<eigene>"
    Wenn das Release "<release>" heißt
    Dann ist ein Update verfügbar: "<neuer>"

    Beispiele:
      | eigene | release | neuer |
      | 0.1.0  | v0.2.0  | ja    |
      | 0.9.0  | 0.10.0  | ja    |
      | 0.2.0  | v0.2.0  | nein  |
      | 0.2.0  | v0.1.9  | nein  |
      | 0.1.0  | latest  | nein  |

  Szenario: Eine neuere Version wird nach dem Start gemeldet
    Angenommen die App hat die Version "0.1.0" und das Release heißt "v0.2.0"
    Wenn die App startet
    Dann zeigt die Seitenleiste "Version 0.2.0 verfügbar"
    Und die Karte bietet "Ansehen" und "Später"

  Szenario: Ohne neuere Version erscheint keine Karte
    Angenommen die App ist auf dem neuesten Stand
    Wenn die App startet
    Dann gibt es keine Hinweiskarte

  Szenario: Ein Verbindungsfehler beim Start bleibt still
    Angenommen die Abfrage schlägt fehl
    Wenn die App startet
    Dann gibt es keine Hinweiskarte und keinen Fehlerdialog
    Und die App ist bedienbar

  Szenario: „Später“ blendet nur diese Version aus
    Angenommen die Karte für "0.2.0" ist sichtbar
    Wenn ich "Später" wähle
    Dann verschwindet die Karte
    Und beim nächsten Start bleibt sie für "0.2.0" aus
    Und für "0.3.0" erscheint sie wieder

  Szenario: „Ansehen“ öffnet die Release-Seite
    Angenommen die Karte ist sichtbar
    Wenn ich "Ansehen" wähle
    Dann wird die Adresse der Release-Seite im Browser geöffnet

  Szenario: Manuelle Prüfung meldet das Ergebnis ausdrücklich
    Angenommen die App ist auf dem neuesten Stand
    Wenn ich "Datei → Nach Updates suchen…" wähle
    Dann meldet die Statusleiste, dass die App aktuell ist

  Szenario: Manuelle Prüfung ohne Verbindung
    Angenommen die Abfrage schlägt fehl
    Wenn ich "Datei → Nach Updates suchen…" wähle
    Dann meldet die Statusleiste "Keine Verbindung"

  Szenario: Manuelle Prüfung zeigt eine ausgeblendete Version wieder
    Angenommen ich habe "0.2.0" ausgeblendet
    Wenn ich "Datei → Nach Updates suchen…" wähle
    Dann erscheint die Karte wieder

  Szenario: Die Prüfung läuft höchstens einmal am Tag
    Angenommen die letzte Prüfung liegt weniger als 24 Stunden zurück
    Wenn die App startet
    Dann fragt sie nicht erneut ab

  Szenario: Die Prüfung lässt sich abschalten
    Angenommen die Einstellung "update_pruefung" ist aus
    Wenn die App startet
    Dann fragt sie nicht ab
    Aber die manuelle Prüfung funktioniert weiter

  Szenario: Die Abfrage enthält keine App-Daten
    Wenn die App abfragt
    Dann besteht die Anfrage nur aus der Adresse und dem User-Agent mit Programmname und Version
