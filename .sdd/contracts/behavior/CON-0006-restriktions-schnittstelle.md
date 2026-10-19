---
id: CON-0006
project: ""                # PRJ-XXXX
title: "Restriktions-Schnittstelle"
type: behavior
format: gherkin
spec: SPEC-0003
version: 0.1.0
status: review
artifact: ".sdd/contracts/behavior/restriktions-schnittstelle.feature"
tests: ["TST-0006"]
---

# Contract: Restriktions-Schnittstelle

> **Spec:** SPEC-0003 · **Typ:** Verhalten (Gherkin) · **Status:** review

## Zweck

Verhalten der Restriktions-Registry und der Konfiguration.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/restriktions-schnittstelle.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Unbekannte oder doppelte Restriktionen führen zu einem Fehler vor dem Solverlauf.
- **INV-02:** Grundregeln sind wie eigene Regeln konfigurierbar.

## Begriffe

<!-- Domänensprache, die in den Szenarien verwendet wird -->

| Begriff   | Definition |
|-----------|------------|
| ...       | ...        |
