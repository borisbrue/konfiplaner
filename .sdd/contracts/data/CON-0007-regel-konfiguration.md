---
id: CON-0007
project: ""                # PRJ-XXXX
title: "Regel-Konfiguration"
type: data
format: json-schema
spec: SPEC-0003
version: 0.1.0
status: approved
artifact: ".sdd/contracts/data/regel-konfiguration.schema.json"
tests: ["TST-0007"]
---

# Contract: Regel-Konfiguration

> **Spec:** SPEC-0003 · **Typ:** Daten (JSON Schema) · **Status:** review

## Zweck

Datenform der Regel-Konfiguration (YAML, als JSON Schema validiert).

## Invarianten

Diese Regeln MÜSSEN für jede gültige Instanz gelten:

- **INV-01:** Typ ist `hart`, `weich` oder `aus`.
- **INV-02:** Gewicht > 0, Standard 1.

## Beispiele

**Gültig:**
```json
{
  "restriktionen": {
    "mindestanzahl": {"typ": "hart"},
    "schwerpunkte": {"typ": "weich", "gewicht": 5},
    "nicht_zusammen": {"typ": "hart", "parameter": {"person_a": "Anna", "person_b": "Ben"}}
  }
}
```

**Ungültig (und warum):**
```json
{"restriktionen": {"schwerpunkte": {"typ": "vielleicht", "gewicht": 0}}}
```
→ Verstößt gegen INV-01 (Typ) und INV-02 (Gewicht muss > 0 sein).

## Validierung

- Schema unter `.sdd/contracts/data/regel-konfiguration.schema.json` (JSON Schema Draft 2020-12)
- Validatoren je nach Sprache: `ajv` (JS), `jsonschema` (Python), etc.
