---
id: CON-0013
project: ""                # PRJ-XXXX
title: "Konferenzplanung Verhalten"
type: behavior
format: gherkin
spec: SPEC-0008
version: 0.1.0
status: approved
artifact: ".sdd/contracts/behavior/konferenzplanung-verhalten.feature"
tests: ["TST-0016"]
---

# Contract: Konferenzplanung Verhalten

> **Spec:** SPEC-0008 · **Typ:** Verhalten (Gherkin) · **Status:** draft

## Zweck

Verhalten der Konferenzplanung mit festen Terminen, Rangfolge und sichtbaren Konflikten.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/konferenzplanung-verhalten.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Ein Thema mit Festterminen findet genau in diesen Zeitfenstern statt; der Solver verschiebt nichts.
- **INV-02:** Niemand ist gleichzeitig in zwei Terminen; bei Konflikt entscheidet die Rangfolge FK I vor II vor III.
- **INV-03:** Jede entgangene Teilnahme ist ein sichtbarer Verstoß.

## Begriffe

| Begriff | Definition |
|---|---|
| Festtermin | Zeitfenster (Tag, Start, Ende) einer Konferenz aus dem Blatt `Konferenzen` |
| Abschnitt | Kleinste Zeiteinheit des abgeleiteten Zeitrasters zwischen zwei Terminkanten eines Tages |
| Rangfolge | Reihenfolge der Konferenzen einer Person: Fachkonferenz I, II, III |
| Rangfaktor | Kosten einer entgangenen Teilnahme: 100 für I, 10 für II, 1 für weitere (mal Gewicht der Regel) |
| Hauptkonferenz | Übergeordnete Konferenz einer Unterkonferenz; bisher nur Angabe mit Reihenfolge-Warnung |
