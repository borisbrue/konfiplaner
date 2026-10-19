---
id: CON-0001
project: ""                # PRJ-XXXX
title: "Importmodell und Fehlerliste"
type: data
format: json-schema
spec: SPEC-0001
version: 0.1.0
status: review
artifact: ".sdd/contracts/data/importmodell-und-fehlerliste.schema.json"
tests: ["TST-0001"]
---

# Contract: Importmodell und Fehlerliste

> **Spec:** SPEC-0001 · **Typ:** Daten (JSON Schema) · **Status:** review

## Zweck

Form des Importergebnisses: Personen/Themen/Slots und Meldungen mit Blatt, Zeile, Spalte.

## Invarianten

Diese Regeln MÜSSEN für jede gültige Instanz gelten:

- **INV-01:** Bei mindestens einer Meldung der Schwere "fehler" ist `modell` nicht vorhanden.
- **INV-02:** Jede Person hat genau zwei verschiedene Themen.

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

- Schema unter `.sdd/contracts/data/importmodell-und-fehlerliste.schema.json` (JSON Schema Draft 2020-12)
- Validatoren je nach Sprache: `ajv` (JS), `jsonschema` (Python), etc.
