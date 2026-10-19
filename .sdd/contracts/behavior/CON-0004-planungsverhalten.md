---
id: CON-0004
project: ""                # PRJ-XXXX
title: "Planungsverhalten"
type: behavior
format: gherkin
spec: SPEC-0002
version: 0.1.0
status: review
artifact: ".sdd/contracts/behavior/planungsverhalten.feature"
tests: ["TST-0004"]
---

# Contract: Planungsverhalten

> **Spec:** SPEC-0002 · **Typ:** Verhalten (Gherkin) · **Status:** review

## Zweck

Planungsverhalten: Themenabdeckung, Mindestanzahl, Wichtigkeit, Dauer, Reproduzierbarkeit.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/planungsverhalten.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Kein Thema entfällt in einem Plan mit Status `optimal` oder `machbar`.
- **INV-02:** Mindestanzahl gilt pro Termin.
- **INV-03:** Gleiche Eingabe + gleicher Seed → gleicher Plan.

## Begriffe

<!-- Domänensprache, die in den Szenarien verwendet wird -->

| Begriff   | Definition |
|-----------|------------|
| ...       | ...        |
