---
id: CON-0018
project: ""                # PRJ-XXXX
title: "Verteilungsbrett Verhalten"
type: behavior
format: gherkin
spec: SPEC-0013
version: 0.1.0
status: approved
artifact: ".sdd/contracts/behavior/verteilungsbrett-verhalten.feature"
tests: ["TST-0026"]
---

# Contract: Verteilungsbrett Verhalten

> **Spec:** SPEC-0013 · **Typ:** Verhalten (Gherkin) · **Status:** draft

## Zweck

Verschieben von Lehrkräften zwischen Konferenzen auf dem Brett.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/verteilungsbrett-verhalten.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Brett, Termine, Personen, Themen und Hinweise zeigen nach jeder Verschiebung dieselbe Verteilung.
- **INV-02:** Der Vorsitz ist nie verschiebbar und immer in seiner Konferenz.
- **INV-03:** Eine Verschiebung speichert eine feste Zuweisung und lässt sich rückgängig machen.

## Begriffe

| Begriff | Definition |
|---|---|
| Brett | Ansicht mit einer Spalte je Konferenz; Karten sind Lehrkräfte |
| Set | Die möglichen Konferenzen einer Lehrkraft |
| Ausnahme | Ablegen in einer Konferenz außerhalb des Sets; sie wird ans Ende des Sets gesetzt |
| Zuweisung | Feste Teilnahme einer Lehrkraft an einer Konferenz (SPEC-0012 FR-09) |
| Prüfhinweis | Meldung zu Mindestanzahl, Vorsitz oder Überschneidung nach einer Änderung |
