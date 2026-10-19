---
id: CON-0009
project: ""                # PRJ-XXXX
title: "Export Verhalten"
type: behavior
format: gherkin
spec: SPEC-0004
version: 0.1.0
status: review
artifact: ".sdd/contracts/behavior/export-verhalten.feature"
tests: ["TST-0009"]
---

# Contract: Export Verhalten

> **Spec:** SPEC-0004 · **Typ:** Verhalten (Gherkin) · **Status:** review

## Zweck

Beobachtbares Exportverhalten inkl. Überschreibschutz.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/export-verhalten.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Bestehende Dateien werden nie ohne Bestätigung überschrieben.

## Begriffe

<!-- Domänensprache, die in den Szenarien verwendet wird -->

| Begriff   | Definition |
|-----------|------------|
| ...       | ...        |
