---
id: CON-0005
project: ""                # PRJ-XXXX
title: "Planungsdauer"
type: performance
format: slo-yaml
spec: SPEC-0002
version: 0.1.0
status: review
artifact: ".sdd/contracts/performance/planungsdauer.slo.yaml"
tests: ["TST-0005"]
---

# Contract: Planungsdauer

> **Spec:** SPEC-0002 · **Typ:** Performance (SLO) · **Status:** review

## Service Level Objectives (SLOs)

| SLI                     | Ziel       | Messfenster | Konsequenz bei Verletzung      |
|-------------------------|------------|-------------|-------------------------------|
| Latenz p95 (GET /...)   | < 200 ms   | 30 Tage     | Alert + Rollback-Kandidat     |
| Verfügbarkeit           | ≥ 99.9 %   | 30 Tage     | Incident Review               |
| Fehlerquote (5xx)       | < 0.1 %    | 24 Stunden  | Auto-Page                     |

## Messung

- **Datenquelle:** <z.B. Prometheus, Datadog>
- **Erhebung:** <z.B. RED-Metrics auf API-Gateway>
- **Tests:** Lasttests mit k6/Locust/Gatling laufen vor jedem Release

## Error Budget

Wird das Budget innerhalb des Messfensters verbraucht, gilt ein Feature-Freeze, bis die SLOs wieder eingehalten werden.
