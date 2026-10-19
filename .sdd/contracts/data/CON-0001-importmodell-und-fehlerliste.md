---
id: CON-0001
project: ""                # PRJ-XXXX
title: "Importmodell und Fehlerliste"
type: data
format: json-schema
spec: SPEC-0001
version: 0.1.0
status: approved
artifact: ".sdd/contracts/data/importmodell-und-fehlerliste.schema.json"
tests: ["TST-0001"]
---

# Contract: Importmodell und Fehlerliste

> **Spec:** SPEC-0001 · **Typ:** Daten (JSON Schema) · **Status:** approved

## Zweck

Form des Importergebnisses: Personen/Themen/Slots und Meldungen mit Blatt, Zeile, Spalte.

## Invarianten

Diese Regeln MÜSSEN für jede gültige Instanz gelten:

- **INV-01:** Bei mindestens einer Meldung der Schwere "fehler" ist `modell` nicht vorhanden. Fehlt das Blatt `Zeitslots`, liefert der Import die Eingabedaten ohne Slots (die GUI ergänzt sie).
- **INV-02:** Jede Person hat genau zwei verschiedene Themen.

## Beispiele

**Gültig:**
```json
{
  "meldungen": [{"schwere": "warnung", "blatt": "Personen", "zeile": 7, "spalte": "Name", "text": "Name kommt doppelt vor"}],
  "modell": {
    "personen": [{"name": "Anna", "themen": ["Abendmahl", "Taufe"]}],
    "themen": [{"name": "Abendmahl", "wichtigkeit": 3, "mindestanzahl": 2, "dauer_min": 45}]
  }
}
```

**Ungültig (und warum):**
```json
{"meldungen": [{"schwere": "fehler", "blatt": "Personen", "zeile": 3, "spalte": "Thema 2", "text": "Unbekanntes Thema"}],
 "modell": {"personen": [], "themen": []}}
```
→ Verstößt gegen INV-01 (Modell trotz Fehler).

## Validierung

- Schema unter `.sdd/contracts/data/importmodell-und-fehlerliste.schema.json` (JSON Schema Draft 2020-12)
- Validatoren je nach Sprache: `ajv` (JS), `jsonschema` (Python), etc.
