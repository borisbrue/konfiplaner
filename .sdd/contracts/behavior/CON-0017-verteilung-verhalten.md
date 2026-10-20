---
id: CON-0017
project: ""                # PRJ-XXXX
title: "Verteilung Verhalten"
type: behavior
format: gherkin
spec: SPEC-0012
version: 0.1.0
status: approved
artifact: ".sdd/contracts/behavior/verteilung-verhalten.feature"
tests: ["TST-0024"]
---

# Contract: Verteilung Verhalten

> **Spec:** SPEC-0012 · **Typ:** Verhalten (Gherkin) · **Status:** draft

## Zweck

Verteilung der Lehrkräfte auf ihre Konferenzen mit Profil, Rangfolge und Ausgleich.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/verteilung-verhalten.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Jede Lehrkraft mit Konferenz nimmt in jedem Plan an mindestens einer teil (Regel `verteilung` hart).
- **INV-02:** Mindestanzahl und Vorsitz sind harte Grenzen; Rangfolge und Ausgleich sind weich.
- **INV-03:** Nicht besuchte Konferenzen erzeugen keine Verstoßmeldung.

## Begriffe

| Begriff | Definition |
|---|---|
| Set | Die möglichen Konferenzen einer Lehrkraft (FK I, II, III, manuell ergänzt) |
| Verteilen | Jede Lehrkraft nimmt an mindestens einer Konferenz ihres Sets teil, der Rest verteilt sich |
| Zielgröße | Lehrkräfte mit Konferenz geteilt durch Konferenzen, gerundet, mindestens 1 |
| Ausgleich | Weiche Regel: Teilnehmerzahlen möglichst nahe an der Zielgröße |
| Rangfolge | Weiche Regel: Vorliebe für die erste, dann die zweite Konferenz |
