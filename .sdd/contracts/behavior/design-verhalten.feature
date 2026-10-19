# language: de
Funktionalität: Visuelles Design im Dark Mode (SPEC-0011, CON-0016)
  Als Planer:in
  möchte ich eine ruhige, lesbare dunkle Oberfläche
  um lange damit zu arbeiten

  Szenario: Dunkles Design ist aktiv
    Wenn die App startet
    Dann ist die Fensterfläche dunkel und der Text hell mit ausreichendem Kontrast

  Szenario: Seitenleiste ersetzt die Tab-Leiste
    Angenommen eine geladene Datei
    Dann zeigt die Seitenleiste die Schritte Daten, Konferenzen, Lehrkräfte, Regeln, Planen und Ergebnis
    Und jeder Schritt zeigt einen Kurzstatus

  Szenario: Kurzstatus folgt dem Stand
    Angenommen eine geladene Lehrerliste und ich wähle eine Konferenz ab
    Dann zeigt der Schritt "Konferenzen" "25 von 26 ausgewählt"

  Szenario: Gesperrte Schritte
    Angenommen keine Datei ist geladen
    Dann sind alle Schritte außer "Daten" gesperrt und lassen sich nicht öffnen

  Szenario: Wechsel per Seitenleiste und Tastatur
    Wenn ich in der Seitenleiste "Planen" wähle oder Strg+5 drücke
    Dann zeigt das Fenster die Seite "Planen"
    Und der Seitenkopf nennt den Titel und einen erklärenden Satz

  Szenario: Primäre Aktion
    Angenommen die Seite "Planen"
    Dann ist "Planen" in der Akzentfarbe hervorgehoben und "Abbrechen" neutral

  Szenario: Fachfarbe ist überall gleich
    Angenommen die Konferenz "Deutsch" kommt in mehreren Ansichten vor
    Dann hat sie überall dieselbe Farbe und ihren Namen daneben

  Szenario: Leerer Zustand nennt den nächsten Schritt
    Angenommen keine Datei ist geladen
    Dann nennt die Seite "Daten" "Excel-Datei öffnen oder hier ablegen"

  Szenario: Datei ablegen
    Wenn ich eine .xlsx-Datei auf das Fenster ziehe
    Dann wird sie geladen

  Szenario: Falsches Dateiformat ablegen
    Wenn ich eine andere Datei auf das Fenster ziehe
    Dann wird sie ignoriert und die Statuszeile nennt den Grund

  Szenario: Fokus ist sichtbar
    Wenn ich mit Tab durch die Elemente gehe
    Dann zeigt jedes Element einen sichtbaren Fokusring

  Szenario: Statusfarben mit Text
    Angenommen eine Lehrkraft ist "neu zu verplanen"
    Dann steht der Status als Text in der Tabelle und ist farblich hervorgehoben

  Szenario: Kleine Bildschirme
    Wenn das Fenster 1024 mal 600 Pixel groß ist
    Dann ist jede Seite bedienbar
