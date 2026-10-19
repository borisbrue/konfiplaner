---
id: CON-0014
project: ""                # PRJ-XXXX
title: "Konferenzauswahl Verhalten"
type: behavior
format: gherkin
spec: SPEC-0009
version: 0.1.0
status: approved
artifact: ".sdd/contracts/behavior/konferenzauswahl-verhalten.feature"
tests: ["TST-0018"]
---

# Contract: Konferenzauswahl Verhalten

> **Spec:** SPEC-0009 · **Typ:** Verhalten (Gherkin) · **Status:** draft

## Zweck

Wirkung der Konferenzauswahl auf Modell, Plan und GUI.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/konferenzauswahl-verhalten.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Abgewählte Konferenzen kommen in keinem Plan, keiner Teilnehmerliste und keinem Verstoß vor.
- **INV-02:** Die Reihenfolge der übrigen Konferenzen einer Person bleibt erhalten.
- **INV-03:** „Neu zuordnen" und „Ohne Konferenz" sind disjunkt.

## Begriffe

| Begriff | Definition |
|---|---|
| Auswahl | Menge der stattfindenden Konferenzen; gespeichert werden die abgewählten |
| Nachrücken | Die übrigen Konferenzen einer Person behalten ihre Reihenfolge, die nächste wird die erste |
| Neu zuordnen | Personen, die durch die Auswahl keine Konferenz mehr haben |
| Ohne Konferenz | Personen, die schon in der Datei keine Konferenz hatten |
