---
id: CON-0010
project: ""                # PRJ-XXXX
title: "GUI-Abläufe"
type: behavior
format: gherkin
spec: SPEC-0005
version: 0.1.0
status: approved
artifact: ".sdd/contracts/behavior/gui-ablaeufe.feature"
tests: ["TST-0010"]
---

# Contract: GUI-Abläufe

> **Spec:** SPEC-0005 · **Typ:** Verhalten (Gherkin) · **Status:** approved

## Zweck

GUI-Abläufe von Import bis Export.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/gui-ablaeufe.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Die GUI enthält keine Fachlogik und bleibt während der Planung bedienbar.

## Begriffe

| Begriff | Definition |
|---|---|
| Sitzung | Qt-freie Anwendungsschicht mit Zustand und Abläufen; die GUI zeigt sie nur an |
| Schritte | Seiten Daten, Regeln, Planen, Ergebnis; Export über Schaltfläche/Menü |
| Planbar | Datei ohne Fehler geladen und mindestens ein Zeitslot vorhanden |
| Einstellungsspeicher | Qt-unabhängige Persistenz (Standard: YAML-Datei in der Benutzerkonfiguration) |
