---
id: CON-0003
project: ""                # PRJ-XXXX
title: "Domänenmodell und Plan"
type: data
format: json-schema
spec: SPEC-0002
version: 0.1.0
status: review
artifact: ".sdd/contracts/data/domaenenmodell-und-plan.schema.json"
tests: ["TST-0003"]
---

# Contract: Domänenmodell und Plan

> **Spec:** SPEC-0002 · **Typ:** Daten (JSON Schema) · **Status:** review

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
  "id": "01HZ...",
  "name": "Beispiel"
}
```

**Ungültig (und warum):**
```json
{
  "id": "",
  "name": null
}
```
→ Verstößt gegen INV-01 (id darf nicht leer sein).

## Validierung

- Schema unter `.sdd/contracts/data/domaenenmodell-und-plan.schema.json` (JSON Schema Draft 2020-12)
- Validatoren je nach Sprache: `ajv` (JS), `jsonschema` (Python), etc.
