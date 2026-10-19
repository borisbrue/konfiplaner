---
id: CON-0016
project: ""                # PRJ-XXXX
title: "Design Verhalten"
type: behavior
format: gherkin
spec: SPEC-0011
version: 0.1.0
status: approved
artifact: ".sdd/contracts/behavior/design-verhalten.feature"
tests: ["TST-0022"]
---

# Contract: Design Verhalten

> **Spec:** SPEC-0011 · **Typ:** Verhalten (Gherkin) · **Status:** draft

## Zweck

Sichtbares Verhalten des dunklen Designs.

## Garantien

Die im Artifact (`.sdd/contracts/behavior/design-verhalten.feature`) hinterlegten Szenarien sind **ausführbare Spezifikation**.
Jedes Szenario MUSS durch einen automatisierten Test (z.B. Cucumber, behave, SpecFlow) abgedeckt sein.

## Invarianten (über alle Szenarien hinweg)

- **INV-01:** Text-/Flächenkontrast mindestens 4,5:1, Fachfarben mindestens 3:1.
- **INV-02:** Eine Konferenz hat in allen Ansichten dieselbe Farbe und immer ihren Namen daneben.
- **INV-03:** Das Design ändert keine Funktion.

## Begriffe

| Begriff | Definition |
|---|---|
| Fachfarbe | Stabile Farbe einer Konferenz, abgeleitet aus ihrem Namen |
| Seitenleiste | Liste der Ablaufschritte mit Nummer, Name und Kurzstatus |
| Kurzstatus | Eine kurze Zeile unter dem Schrittnamen, z. B. „17 von 26 ausgewählt" |
| Design-Tokens | Benannte Farben, Radien, Abstände und Größen an einer Stelle |
