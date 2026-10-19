---
id: CON-0005
project: ""                # PRJ-XXXX
title: "Planungsdauer"
type: performance
format: slo-yaml
spec: SPEC-0002
version: 0.1.0
status: approved
artifact: ".sdd/contracts/performance/planungsdauer.slo.yaml"
tests: ["TST-0005"]
---

# Contract: Planungsdauer

> **Spec:** SPEC-0002 · **Typ:** Performance (SLO) · **Status:** approved

## Service Level Objectives (SLOs)

| SLI                              | Ziel          | Messfenster | Konsequenz bei Verletzung            |
|----------------------------------|---------------|-------------|--------------------------------------|
| Planungsdauer 500 P / 30 T / 40 S | ≤ 60 s        | je Lauf     | Performance-Test schlägt fehl        |
| Reproduzierbarkeit (1 Worker)    | 100 % identisch | je Lauf   | Test schlägt fehl                    |

## Messung

- **Datenquelle:** Synthetische, per Seed erzeugte Instanz im Performance-Test
- **Erhebung:** Wanduhrzeit von Aufruf `Planer.planen` bis Ergebnis (inkl. Modellaufbau)
- **Tests:** pytest-Performance-Test (TST-0005), Referenzhardware: Steam Deck bzw. gleichwertig

## Error Budget

Es gibt kein Budget: Die Ziele gelten pro Lauf; eine Verletzung blockiert den Merge.
