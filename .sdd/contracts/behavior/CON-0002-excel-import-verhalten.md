---
id: CON-0002
project: ""                # PRJ-XXXX
title: "Excel-Import Verhalten"
type: behavior
format: gherkin
spec: SPEC-0001
version: 0.1.0
status: review
artifact: ".sdd/contracts/behavior/excel-import-verhalten.feature"
tests: ["TST-0002"]
---

# Contract: Excel-Import Verhalten

> **Spec:** SPEC-0001 · **Typ:** Verhalten (Gherkin) · **Status:** review

## Zweck

Beobachtbares Importverhalten inklusive Fehlertoleranz bei Überschriften.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/excel-import-verhalten.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Alle Fehler werden gesammelt gemeldet, nicht nur der erste.

## Begriffe

<!-- Domänensprache, die in den Szenarien verwendet wird -->

| Begriff   | Definition |
|-----------|------------|
| ...       | ...        |
