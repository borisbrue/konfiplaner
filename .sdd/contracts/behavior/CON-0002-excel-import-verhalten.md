---
id: CON-0002
project: ""                # PRJ-XXXX
title: "Excel-Import Verhalten"
type: behavior
format: gherkin
spec: SPEC-0001
version: 0.1.0
status: approved
artifact: ".sdd/contracts/behavior/excel-import-verhalten.feature"
tests: ["TST-0002"]
---

# Contract: Excel-Import Verhalten

> **Spec:** SPEC-0001 · **Typ:** Verhalten (Gherkin) · **Status:** approved

## Zweck

Beobachtbares Importverhalten inklusive Fehlertoleranz bei Überschriften.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/excel-import-verhalten.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Alle Fehler werden gesammelt gemeldet, nicht nur der erste.

## Begriffe

| Begriff | Definition |
|---|---|
| Meldung | Eintrag der Fehlerliste: Schwere (`fehler`/`warnung`), Blatt, Zeile (Excel-Zeile), Spalte, Text |
| Minimalformat | Blatt `Personen` mit Name, Thema 1, Thema 2 |
| Standardwerte | Wichtigkeit 3, Mindestanzahl 1, Dauer 45 Minuten für Themen ohne Blatt `Themen` |
| Slot | Zeile des Blatts `Zeitslots`, identifiziert durch Tag + Start |
