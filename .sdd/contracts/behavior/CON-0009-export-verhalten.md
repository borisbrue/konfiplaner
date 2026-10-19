---
id: CON-0009
project: ""                # PRJ-XXXX
title: "Export Verhalten"
type: behavior
format: gherkin
spec: SPEC-0004
version: 0.1.0
status: approved
artifact: ".sdd/contracts/behavior/export-verhalten.feature"
tests: ["TST-0009"]
---

# Contract: Export Verhalten

> **Spec:** SPEC-0004 · **Typ:** Verhalten (Gherkin) · **Status:** approved

## Zweck

Beobachtbares Exportverhalten inkl. Überschreibschutz.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/export-verhalten.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Bestehende Dateien werden nie ohne Bestätigung überschrieben.

## Begriffe

| Begriff | Definition |
|---|---|
| Plan | Solver-unabhängiges Ergebnis (CON-0003) mit Status, Terminen, Verstößen, Begründung, Warnungen |
| Termin-Zeile | Zeile im Blatt `Termine`: Tag, Start, Ende, Thema, Teilnehmerzahl, Teilnehmende |
| Erfüllt | `ja`, wenn jeder Termin des Themas die Mindestanzahl erreicht und mindestens ein Termin existiert, sonst `nein` |
| Hinweis | Zeile im Blatt `Hinweise` mit Art (`Warnung`, `Verstoß`, `Begründung`, `Status`) und Text |
| Bestätigung | Ausdrückliche Freigabe (`ueberschreiben=True`) zum Überschreiben einer vorhandenen Datei |
