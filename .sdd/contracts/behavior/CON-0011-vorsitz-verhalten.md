---
id: CON-0011
project: ""                # PRJ-XXXX
title: "Vorsitz Verhalten"
type: behavior
format: gherkin
spec: SPEC-0006
version: 0.1.0
status: approved
artifact: ".sdd/contracts/behavior/vorsitz-verhalten.feature"
tests: ["TST-0012"]
---

# Contract: Vorsitz Verhalten

> **Spec:** SPEC-0006 · **Typ:** Verhalten (Gherkin) · **Status:** draft

## Zweck

Verhalten der Vorsitz-Regel in Planung, Import, Export und GUI.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/vorsitz-verhalten.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** In jedem Plan mit Status `optimal` oder `machbar` und harter Regel `vorsitz` ist der Vorsitz in allen Terminen seines Themas.
- **INV-02:** Der Vorsitz zählt zur Mindestanzahl; pro Thema gibt es höchstens einen Vorsitz.
- **INV-03:** Dateien ohne Spalte `Vorsitz` verhalten sich wie vor SPEC-0006.

## Begriffe

| Begriff | Definition |
|---|---|
| Vorsitz | Person der Personenliste, die ein Thema leitet und in jedem Termin des Themas sein muss |
| Rolle | Spalte im Export-Blatt `Personen`: `Vorsitz` oder `Teilnahme` |
| Regel `vorsitz` | Grundregel, Standard hart, wie jede Grundregel hart/weich/aus konfigurierbar |
