---
id: CON-0008
project: ""                # PRJ-XXXX
title: "Export-Blattstruktur"
type: data
format: json-schema
spec: SPEC-0004
version: 0.1.0
status: review
artifact: ".sdd/contracts/data/export-blattstruktur.schema.json"
tests: ["TST-0008"]
---

# Contract: Export-Blattstruktur

> **Spec:** SPEC-0004 · **Typ:** Daten (JSON Schema) · **Status:** review

## Zweck

Blatt- und Spaltenstruktur der Exportdatei.

## Invarianten

Diese Regeln MÜSSEN für jede gültige Instanz gelten:

- **INV-01:** Genau die Blätter Termine, Personen, Themen, Hinweise in dieser Spaltenreihenfolge.

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

- Schema unter `.sdd/contracts/data/export-blattstruktur.schema.json` (JSON Schema Draft 2020-12)
- Validatoren je nach Sprache: `ajv` (JS), `jsonschema` (Python), etc.
