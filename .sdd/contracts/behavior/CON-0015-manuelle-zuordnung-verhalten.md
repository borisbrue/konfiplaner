---
id: CON-0015
project: ""                # PRJ-XXXX
title: "Manuelle Zuordnung Verhalten"
type: behavior
format: gherkin
spec: SPEC-0010
version: 0.1.0
status: approved
artifact: ".sdd/contracts/behavior/manuelle-zuordnung-verhalten.feature"
tests: ["TST-0020"]
---

# Contract: Manuelle Zuordnung Verhalten

> **Spec:** SPEC-0010 · **Typ:** Verhalten (Gherkin) · **Status:** draft

## Zweck

Manuelle Zuordnung, Fixierungen und Teilneuplanung.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/manuelle-zuordnung-verhalten.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Eine Teilneuplanung ändert die Teilnahme keiner nicht markierten Lehrkraft.
- **INV-02:** Eine feste Teilnahme bleibt in jedem Plan erhalten, sonst gibt es keinen Plan mit Begründung.
- **INV-03:** Jede Änderung markiert die betroffene Lehrkraft; nur erfolgreiche Planung löscht die Markierung.

## Begriffe

| Begriff | Definition |
|---|---|
| Änderung | Manuelle Abweichung einer Lehrkraft von der Datei: Konferenzen, gesperrte Termine, feste Termine |
| Markiert | Lehrkraft, die bei der Teilneuplanung neu verplant wird |
| Fixierung | Harte Vorgabe an den Solver: feste Teilnahme oder feste Startslots |
| Teilneuplanung | Neuberechnung nur der markierten Lehrkräfte, der Rest bleibt wie im Plan |
