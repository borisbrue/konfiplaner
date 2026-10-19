---
id: CON-0006
project: ""                # PRJ-XXXX
title: "Restriktions-Schnittstelle"
type: behavior
format: gherkin
spec: SPEC-0003
version: 0.1.0
status: approved
artifact: ".sdd/contracts/behavior/restriktions-schnittstelle.feature"
tests: ["TST-0006"]
---

# Contract: Restriktions-Schnittstelle

> **Spec:** SPEC-0003 · **Typ:** Verhalten (Gherkin) · **Status:** approved

## Zweck

Verhalten der Restriktions-Registry und der Konfiguration.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/restriktions-schnittstelle.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Doppelte Namen führen bei der Registrierung zu einem Fehler; unbekannte Regeln oder fehlerhafte Parameter führen vor dem Solverlauf zu einem Fehler mit Regelname.
- **INV-02:** Grundregeln und Plugin-Regeln haben dieselbe Konfigurationsform (typ, gewicht, parameter).

## Begriffe

| Begriff | Definition |
|---|---|
| Restriktion | Planungsregel mit eindeutigem Namen, Typ, Parametern und Gewicht |
| Grundregel | Mitgelieferte Restriktion: `themenabdeckung`, `mindestanzahl`, `schwerpunkte`, `keine_ueberschneidung`, `verfuegbarkeit`, `wichtigkeit` |
| Typ `hart` / `weich` / `aus` | hart = muss gelten, sonst `kein_plan`; weich = Verstoß kostet Gewicht; aus = nicht angewendet |
| Gewicht | Positive Zahl (Standard 1), Strafe je Verstoß einer weichen Regel |
| Planungskontext | Abstraktion des Solvers, über die Regeln Bedingungen und Strafterme hinzufügen |
| Registry | Verzeichnis aller Restriktionen nach Namen (Dekorator oder Entry-Point) |
| Verstoß | Dokumentierte Verletzung einer weichen Regel |

Standard-Typen der Grundregeln: `themenabdeckung`, `mindestanzahl`, `schwerpunkte`, `keine_ueberschneidung`, `verfuegbarkeit` = hart; `wichtigkeit` = weich.
