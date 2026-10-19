---
id: CON-0012
project: ""                # PRJ-XXXX
title: "Lehrerlisten-Import Verhalten"
type: behavior
format: gherkin
spec: SPEC-0007
version: 0.1.0
status: approved
artifact: ".sdd/contracts/behavior/lehrerlisten-import-verhalten.feature"
tests: ["TST-0014"]
---

# Contract: Lehrerlisten-Import Verhalten

> **Spec:** SPEC-0007 · **Typ:** Verhalten (Gherkin) · **Status:** draft

## Zweck

Verhalten des Lehrerlisten-Imports samt Normalisierung der Konferenznamen.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/lehrerlisten-import-verhalten.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Nur Zuordnungen mit Status `sicher` (bestätigt oder exakter Treffer) führen zu einem Modell; `vorschlag` und `unbekannt` sind Fehler.
- **INV-02:** Eine Person hat 0 bis n verschiedene Konferenzen in der Reihenfolge der Spalten.
- **INV-03:** Jede Konferenz hat höchstens einen Vorsitz.

## Begriffe

| Begriff | Definition |
|---|---|
| Rohwert | Text einer Konferenzzelle, wie er in der Liste steht |
| Schlüssel | Rohwert ohne Beachtung von Groß-/Kleinschreibung, mit bereinigten Leerzeichen auch um `/` und `,` |
| Konferenzsatz | Menge der einheitlichen Konferenznamen (aus der Spalte Vorsitzende, sonst einfache Werte) |
| Status | `sicher` (bestätigt oder exakter Treffer), `vorschlag` (abgeleitet, unbestätigt), `unbekannt` |
| Zuordnung | Rohwert → Liste von Konferenzen; bestätigt und gespeichert |
