---
id: CON-0019
project: ""                # PRJ-XXXX
title: "Tagesplan und Einladung Verhalten"
type: behavior
format: gherkin
spec: SPEC-0014
version: 0.1.0
status: approved
artifact: ".sdd/contracts/behavior/tagesplan-und-einladung-verhalten.feature"
tests: ["TST-0028", "TST-0029"]
---

# Contract: Tagesplan und Einladung Verhalten

> **Spec:** SPEC-0014 · **Typ:** Verhalten (Gherkin) · **Status:** draft

## Zweck

Tagesablauf bearbeiten und daraus die Einladung als Word-Dokument erzeugen.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/tagesplan-und-einladung-verhalten.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Die Konferenzliste im Dokument entspricht immer der aktuellen Auswahl der App.
- **INV-02:** Ein Export mit Fehlern in der Prüfung schreibt keine Datei.
- **INV-03:** Eine vorhandene Zieldatei wird nie ohne Bestätigung überschrieben.

## Begriffe

| Begriff | Definition |
|---|---|
| Tagesplan | Kopf (Datum, Titel, Thema, Ziele …) und geordnete Zeitblöcke |
| Block | Eine Zeile der Ablauftabelle: Zeit, Titel, Inhalt, Wer/Wie |
| Konferenzblock | Block, der die gewählten Fachkonferenzen automatisch einträgt |
