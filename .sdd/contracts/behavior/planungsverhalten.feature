# language: de
Funktionalität: Planung (SPEC-0002, CON-0004)
  Als Planer:in
  möchte ich einen Terminplan berechnen lassen
  um Personen thematisch passend zu Terminen zusammenzustellen

  Hintergrund:
    Angenommen die Grundregeln stehen auf ihren Standardwerten
    Und Zeitslots dauern jeweils 45 Minuten

  Szenario: Einfacher Plan
    Angenommen die Themen A, B, C mit Mindestanzahl 2 und Dauer 45 Minuten
    Und 12 Personen: je 4 mit (A,B), (B,C), (A,C)
    Und 6 Zeitslots, alle Personen immer verfügbar
    Wenn ich plane
    Dann ist der Status "optimal"
    Und es gibt zu jedem der Themen A, B, C mindestens einen Termin
    Und jede Person nimmt an einem Termin jedes ihrer beiden Themen teil

  Szenario: Nur ein Termin je Thema
    Angenommen ein Thema mit Mindestanzahl 3 und genau 3 Personen mit diesem Thema
    Wenn ich plane
    Dann gibt es genau einen Termin dieses Themas mit diesen 3 Personen

  Szenario: Mehrere Termine je Thema
    Angenommen ein Thema mit Mindestanzahl 3 und 6 Personen, die nie gleichzeitig verfügbar sind
    Wenn ich plane
    Dann hat jeder Termin dieses Themas mindestens 3 Teilnehmende

  Szenario: Mindestanzahl nicht erreichbar
    Angenommen ein Thema mit Mindestanzahl 5 und nur 3 Personen mit diesem Thema
    Wenn ich plane
    Dann ist der Status "kein_plan"
    Und die Begründung nennt das Thema und die Regel "mindestanzahl"

  Szenario: Kein Thema entfällt
    Angenommen ein Thema ohne Personen und mit Mindestanzahl 1
    Wenn ich plane
    Dann ist der Status "kein_plan"
    Und die Begründung nennt die Regel "themenabdeckung" und das Thema

  Szenario: Schwerpunkte weich gestellt bei Engpass
    Angenommen zwei Themen, deren gemeinsame Person nur einen gemeinsamen Slot hat
    Und die Regel "schwerpunkte" ist weich
    Wenn ich plane
    Dann ist der Status "optimal" oder "machbar"
    Und die Verstöße nennen "schwerpunkte" und die betroffene Person

  Szenario: Wichtigkeit bei Slot-Konflikt
    Angenommen ein Thema mit Wichtigkeit 5 und eines mit Wichtigkeit 1
    Und beide konkurrieren um denselben besten Slot
    Wenn ich plane
    Dann liegt das Thema mit Wichtigkeit 5 im besseren Slot

  Szenario: Keine Überschneidung bei nur einem möglichen Slotpaar
    Angenommen eine Person mit zwei Themen und genau zwei freien Slots
    Wenn ich plane
    Dann liegen die beiden Termine der Person in verschiedenen Slots

  Szenariogrundriss: Dauer wird aufgerundet
    Angenommen ein Thema mit Dauer <dauer> Minuten
    Wenn ich plane
    Dann belegt der Termin <slots> aufeinanderfolgende Slots

    Beispiele:
      | dauer | slots |
      | 45    | 1     |
      | 90    | 2     |
      | 100   | 3     |

  Szenario: Dauer länger als jeder zusammenhängende Block
    Angenommen ein Thema mit Dauer 180 Minuten und nur Blöcke mit höchstens 2 Slots
    Wenn ich plane
    Dann ist der Status "kein_plan"
    Und die Begründung nennt das Thema und die Dauer

  Szenario: Person ohne Verfügbarkeit
    Angenommen eine Person ohne jede Verfügbarkeit
    Wenn ich plane
    Dann enthält das Ergebnis eine Warnung zu dieser Person

  Szenario: Kollidierende Regeln
    Angenommen zwei harte Regeln, die sich widersprechen
    Wenn ich plane
    Dann ist der Status "kein_plan"
    Und die Begründung nennt beide Regeln

  Szenario: Reproduzierbarkeit
    Angenommen dieselbe Eingabe, derselbe Seed und ein Solver mit einem Worker
    Wenn ich zweimal plane
    Dann sind beide Pläne identisch

  Szenario: Zeitlimit
    Angenommen eine große Instanz und ein Zeitlimit von 5 Sekunden
    Wenn ich plane
    Dann endet die Planung innerhalb des Limits
    Und der Status ist "optimal" oder "machbar"
    Und der Plan erfüllt alle harten Regeln

  Szenario: Abbruch
    Angenommen eine laufende Planung mit Fortschritts-Callback, der beim ersten Aufruf das Abbruchsignal setzt
    Wenn ich plane
    Dann endet die Planung mit der besten bisherigen Lösung
    Und der Callback wurde mindestens einmal aufgerufen

  Szenario: Abbruch vor der ersten Lösung
    Angenommen das Abbruchsignal ist schon vor dem Start gesetzt
    Wenn ich plane
    Dann ist der Status "kein_plan" oder der Plan die bisher beste Lösung
