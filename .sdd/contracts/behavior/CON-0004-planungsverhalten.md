---
id: CON-0004
project: ""                # PRJ-XXXX
title: "Planungsverhalten"
type: behavior
format: gherkin
spec: SPEC-0002
version: 0.1.0
status: approved
artifact: ".sdd/contracts/behavior/planungsverhalten.feature"
tests: ["TST-0004"]
---

# Contract: Planungsverhalten

> **Spec:** SPEC-0002 · **Typ:** Verhalten (Gherkin) · **Status:** approved

## Zweck

Planungsverhalten: Themenabdeckung, Mindestanzahl, Wichtigkeit, Dauer, Reproduzierbarkeit.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/planungsverhalten.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** In einem Plan mit Status `optimal` oder `machbar` findet jedes Thema statt (themenabdeckung ist hart, sonst `kein_plan`).
- **INV-02:** Jeder Termin eines Themas hat mindestens `mindestanzahl` Teilnehmende.
- **INV-03:** Gleiche Eingabe + gleicher Seed + 1 Worker (ohne wirksames Zeitlimit) → gleicher Plan.

## Begriffe

| Begriff | Definition |
|---|---|
| Thema | Inhalt eines Termins mit Wichtigkeit (1–5), Mindestanzahl und Dauer |
| Mindestanzahl | Mindest-Teilnehmerzahl **pro Termin** eines Themas |
| Wichtigkeit | Gewicht 1 (unwichtig) bis 5 (sehr wichtig); wirkt auf Slot-Wahl und Zielfunktion, ein Thema entfällt nie |
| Slot | Zeitfenster fester Länge; Termine belegen aufeinanderfolgende Slots, Dauer wird auf ganze Slots aufgerundet |
| Termin | Stattfinden eines Themas in einem Slot-Block mit Teilnehmenden |
| Schwerpunkte | Die zwei Themen einer Person |
| Status `optimal` | Optimalität bewiesen, alle harten Regeln erfüllt |
| Status `machbar` | Alle harten Regeln erfüllt, Optimalität nicht bewiesen (Zeitlimit/Abbruch) – im UI „nicht optimal" |
| Status `kein_plan` | Keine Lösung; `begruendung` nennt Regeln und Themen |
| Seed | Zufallsstartwert; Reproduzierbarkeit nur mit einem Solver-Worker und ohne wirksames Zeitlimit |
| Verstoß | Verletzung einer weichen Regel, mit Regelname und Text |
