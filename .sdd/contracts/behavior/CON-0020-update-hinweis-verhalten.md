---
id: CON-0020
project: ""                # PRJ-XXXX
title: "Update-Hinweis Verhalten"
type: behavior
format: gherkin
spec: SPEC-0015
version: 0.1.0
status: approved
artifact: ".sdd/contracts/behavior/update-hinweis-verhalten.feature"
tests: ["TST-0030", "TST-0031"]
---

# Contract: Update-Hinweis Verhalten

> **Spec:** SPEC-0015 · **Typ:** Verhalten (Gherkin) · **Status:** draft

## Zweck

Hinweis auf neuere Versionen im öffentlichen Release, ohne die Bedienung zu stören.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/update-hinweis-verhalten.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Ein Netzwerkfehler blockiert oder beendet die App nie.
- **INV-02:** Gemeldet wird nur eine numerisch höhere stabile Version.
- **INV-03:** Die Abfrage enthält keine Plan-, Personen- oder Dateiangaben.

## Begriffe

| Begriff | Definition |
|---|---|
| Release | Veröffentlichte Version des Projekts auf GitHub mit Versions-Tag (`vX.Y.Z`) |
| Hinweiskarte | Karte unten in der Seitenleiste mit „Ansehen“ und „Später“ |
| Ausgeblendet | Für genau diese Version gespeichert; neuere Versionen erscheinen wieder |
