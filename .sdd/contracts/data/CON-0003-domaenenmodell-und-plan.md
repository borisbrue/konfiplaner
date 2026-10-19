---
id: CON-0003
project: ""                # PRJ-XXXX
title: "Domänenmodell und Plan"
type: data
format: json-schema
spec: SPEC-0002
version: 0.1.0
status: approved
artifact: ".sdd/contracts/data/domaenenmodell-und-plan.schema.json"
tests: ["TST-0003"]
---

# Contract: Domänenmodell und Plan

> Schema beschreibt das Ergebnis `Plan`; die Eingabeobjekte (Thema, Person, Zeitslot) sind in `importmodell-und-fehlerliste.schema.json` (CON-0001) definiert. Bei `kein_plan` ist `termine` leer. Bei `optimal` ist `verstoesse` leer oder fehlt. `teilnehmer` enthält Personennamen.

> **Spec:** SPEC-0002 · **Typ:** Daten (JSON Schema) · **Status:** approved

## Zweck

Datenform von Planergebnis (Termine, Teilnehmer, Status, Verstöße).

## Invarianten

Diese Regeln MÜSSEN für jede gültige Instanz gelten:

- **INV-01:** Ein Plan mit Status `kein_plan` enthält eine Begründung.
- **INV-02:** Jeder Termin hat mindestens einen Slot; Teilnehmer je Termin sind eindeutig.

## Beispiele

**Gültig:**
```json
{
  "status": "machbar",
  "seed": 1,
  "termine": [
    {"thema": "Abendmahl", "start_slot": 2, "anzahl_slots": 2, "teilnehmer": ["Anna", "Ben", "Cem"]}
  ],
  "verstoesse": [{"restriktion": "wichtigkeit", "text": "Thema X liegt nicht im besten Slot"}]
}
```

**Ungültig (und warum):**
```json
{"status": "kein_plan", "termine": []}
```
→ Verstößt gegen INV-01 (`begruendung` fehlt bei `kein_plan`).

## Validierung

- Schema unter `.sdd/contracts/data/domaenenmodell-und-plan.schema.json` (JSON Schema Draft 2020-12)
- Validatoren je nach Sprache: `ajv` (JS), `jsonschema` (Python), etc.
