---
id: SPEC-0013
title: "Verteilungsbrett mit Drag and Drop"
type: feature           # feature | bug-fix
status: approved           # draft | review | approved | implemented | deprecated
owner: "Boris Brünen"
created: 2026-10-20
updated: 2026-10-20
version: 0.1.0
priority: high        # low | medium | high | critical
tags: [brett, drag-and-drop, verteilung, gui]
depends_on: ["SPEC-0005", "SPEC-0010", "SPEC-0011", "SPEC-0012"]          # z.B. ["SPEC-0001"]
fr_test_map:
  FR-01: TST-0026
  FR-02: TST-0026
  FR-03: TST-0026
  FR-04: TST-0027
  FR-05: TST-0026
  FR-06: TST-0027
  FR-07: TST-0027
  FR-08: TST-0027
  FR-09: TST-0026
  FR-10: TST-0027
  FR-11: TST-0027
  FR-12: TST-0026
contracts: ["CON-0018"]           # z.B. ["CON-0001"] – MUSS mindestens einen Eintrag enthalten
tests: ["TST-0026", "TST-0027"]               # z.B. ["TST-0001"] – MUSS mindestens einen Eintrag enthalten
---

# Verteilungsbrett mit Drag and Drop

> **Status:** draft · **Owner:** Boris Brünen · **Version:** 0.1.0

## 1. Kontext & Motivation

Nach der ersten automatischen Verteilung (SPEC-0012) will die Planerin Lehrkräfte von Hand verschieben, um die Personen bestmöglich zu verteilen. Jede Lehrkraft hat ein Set möglicher Konferenzen; innerhalb dieses Sets soll das Verschieben leicht gehen, außerhalb bewusst und mit Warnung. Ein Brett mit einer Spalte je Konferenz zeigt auf einen Blick, wer wo sitzt und wo es eng wird.

## 2. Zielsetzung

**Primärziel:** Lehrkräfte lassen sich per Drag and Drop zwischen Konferenzen verschieben; die Folgen (Mindestanzahl, Vorsitz, Überschneidung) sind sofort sichtbar.

**Erfolgskriterien (messbar):**
- [ ] Ein Verschieben dauert eine Geste (Ziehen) oder zwei Eingaben per Tastatur (Karte wählen, Ziel wählen).
- [ ] Nach jeder Verschiebung stimmen Brett, Termine, Personen, Themen und Hinweise überein.
- [ ] Zielspalten im Set und außerhalb des Sets sind beim Ziehen unterscheidbar.
- [ ] Eine Verschiebung lässt sich zurücknehmen.

**Nicht-Ziele (explizit):**
- Kein Verschieben von Konferenzterminen oder des Vorsitzes per Ziehen.
- Kein automatisches Neuberechnen beim Verschieben (das löst die Teilneuplanung aus, SPEC-0010).

## 3. User Stories

| ID    | Als ...   | möchte ich ...                                   | um ...                                         |
|-------|-----------|--------------------------------------------------|------------------------------------------------|
| US-01 | Planer:in | Lehrkräfte per Ziehen in eine andere Konferenz legen | die Verteilung zu verbessern                   |
| US-02 | Planer:in | sehen, welche Konferenzen zu zu klein sind        | gezielt umzuverteilen                          |
| US-03 | Planer:in | die Konferenzen sehen, die eine Lehrkraft zusätzlich besuchen könnte | passende Ziele zu finden            |

## 4. Funktionale Anforderungen

- **FR-01 (Brett):** Das Ergebnis hat als ersten Reiter „Verteilung" mit einem Brett: je Konferenz im Modell eine Spalte, davor eine Spalte „Ohne Zuteilung". Das Brett ist nach dem Planen der Standardreiter.
- **FR-02 (Spaltenkopf):** Der Kopf zeigt Fachfarbe und Name, Zahl der Teilnehmenden, Mindestanzahl und Zielgröße. Liegt die Zahl unter der Mindestanzahl, steht „unter Mindestanzahl" in Text und Farbe.
- **FR-03 (Karten):** Jede Karte zeigt den Namen und die weiteren Konferenzen im Set der Lehrkraft mit Fachfarbe. Der Vorsitz steht als gesperrte Karte oben in seiner Spalte. „Ohne Zuteilung" enthält Lehrkräfte ohne Teilnahme, auch solche ohne Konferenz.
- **FR-04 (Verschieben):** Eine Karte lässt sich in eine andere Spalte ziehen. Liegt die Ziel-Konferenz im Set der Lehrkraft, wird sie dort eingetragen. Liegt sie außerhalb, ist es eine Ausnahme: Die Konferenz kommt ans Ende des Sets der Lehrkraft, und eine Warnung nennt das.
- **FR-05 (Rückmeldung beim Ziehen):** Die Zielspalte zeigt, ob sie im Set liegt (Akzentrahmen) oder außerhalb (gestrichelter Rahmen mit Hinweis „Ausnahme").
- **FR-06 (Wirkung):** Das Verschieben ändert den Plan sofort: Die Lehrkraft verlässt die alte Konferenz und alle überlappenden Termine und nimmt am Termin der neuen teil. Zusätzlich wird eine feste Zuweisung gespeichert (SPEC-0012 FR-09), die bei jeder Neuplanung gilt, bis die Lehrkraft zurückgesetzt wird.
- **FR-07 (Prüfhinweise):** Nach jeder Änderung werden geprüft: Mindestanzahl je Termin, Vorsitz in jedem Termin seiner Konferenz, keine Überschneidung. Verletzungen stehen im Kopf des Bretts und als Warnungen im Plan (Ergebnis und Export). Das Verschieben bleibt trotzdem möglich.
- **FR-08 (Rückgängig):** Die letzten Verschiebungen lassen sich einzeln zurücknehmen (Schaltfläche und Strg+Z); Plan, Set und Zuweisung der Lehrkraft kehren zurück.
- **FR-09 (Tastatur):** Eine gewählte Karte öffnet mit Enter oder dem Kontextmenü „Verschieben nach …“ eine Liste der Konferenzen, markiert nach im Set und Ausnahme.
- **FR-10 (Vorsitz):** Der Vorsitz lässt sich nicht verschieben; die Meldung nennt den Weg („Vorsitz zuerst im Dialog Bearbeiten ändern").
- **FR-11 (Zurücksetzen):** „Zurücksetzen" einer Lehrkraft (SPEC-0010 FR-09) löst ihre feste Zuweisung; der Plan bleibt, bis neu geplant wird.
- **FR-12 (Größe):** Das Brett scrollt waagerecht, jede Spalte hat feste Breite; es ist ab 1024×600 bedienbar.

## 5. Nicht-funktionale Anforderungen

| Kategorie     | Anforderung                                                   |
|---------------|---------------------------------------------------------------|
| Performance   | Verschieben und Neuaufbau des Bretts < 100 ms bei 100/26      |
| Accessibility | Alle Aktionen auch per Tastatur; Zustände nie nur als Farbe   |
| Datenschutz   | Keine Namen im Log                                            |

## 6. Akzeptanzkriterien (Gherkin)

```gherkin
Feature: Verteilungsbrett

  Scenario: Karte in eine andere Konferenz ziehen
    Given ein Plan und eine Lehrkraft mit zwei Konferenzen im Set
    When ich ihre Karte in die andere Spalte ziehe
    Then nimmt sie dort teil und nicht mehr in der alten Konferenz
```

## 7. Edge Cases & Fehlerfälle

- Lehrkraft nimmt an mehreren zeitlich getrennten Konferenzen teil: Ziehen aus einer Spalte entfernt nur diese Teilnahme.
- Ziel-Konferenz hat mehrere Termine: die Lehrkraft kommt in den ersten Termin ohne Überschneidung mit ihrer übrigen Teilnahme.
- Ablegen in dieselbe Spalte ändert nichts.

## 8. Contracts (was wird garantiert)

| Contract-ID | Typ      | Was wird garantiert?                          |
|-------------|----------|-----------------------------------------------|
| CON-0018    | behavior | Verschieben, Prüfhinweise, Rückgängig, Brett  |

## 9. Tests (wie wird verifiziert)

| Test-ID  | Level      | Was prüft der Test?                                          |
|----------|------------|--------------------------------------------------------------|
| TST-0026 | acceptance | Gherkin aus CON-0018: Brett, Ziehen, Menü, Rückmeldung       |
| TST-0027 | unit       | Verschieben, Prüfung, Rückgängig, Persistenz in der Sitzung   |

## 10. Offene Fragen

- [ ] Mehrfachauswahl von Karten zum gemeinsamen Verschieben (spätere Spec).

## 11. Änderungshistorie

| Datum      | Version | Autor        | Änderung            |
|------------|---------|--------------|---------------------|
| 2026-10-20 | 0.1.0   | Boris Brünen | Initiale Erstellung |
