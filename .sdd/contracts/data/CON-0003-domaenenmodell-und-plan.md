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

## LLM Review Notes

1. **Beispiele sind Platzhalter.** Das gültige Beispiel (`id`, `name`) passt nicht zum Schema. `additionalProperties: false` und `required: [status, termine]` machen es ungültig. Das ungültige Beispiel verweist auf "INV-01 (id darf nicht leer sein)", aber INV-01 betrifft `kein_plan` und die Begründung. Beide Beispiele müssen durch echte Plan-Instanzen ersetzt werden.
2. **INV-02 ist nur halb im Schema abgebildet.** "Mindestens ein Slot" wird über `anzahl_slots >= 1` erzwungen, die Eindeutigkeit der Teilnehmer über `uniqueItems`. Das Schema prüft aber nicht, ob die Slots im Zeitraster liegen. Das ist ohne Kontext auch nicht möglich und sollte im Contract ausdrücklich als Solver- oder Validator-Pflicht benannt werden.
3. **INV-01 ist zu schwach.** `begruendung` muss vorhanden sein, darf aber ein leeres Array sein. Es fehlt `minItems: 1`, damit "enthält eine Begründung" wirklich gilt. Der `if` braucht außerdem `required: ["status"]`. Ohne das trifft er auch bei fehlendem `status` zu. Das ist harmlos, weil `status` ohnehin required ist, aber sauberer.
4. **Spec-Lücken gegenüber dem Schema:**
   - FR-01 nennt `Thema`, `Person`, `Zeitslot` und `Plan`. Der Titel verspricht ein "Domänenmodell", das Schema beschreibt aber nur den Plan. Titel und Zweck sollten auf "Plan" eingegrenzt werden, oder die Eingabeobjekte kommen dazu.
   - Der Spec-Edge-Case "Zeitlimit erreicht → Kennzeichen nicht optimal" ist über `machbar` abgedeckt. Das sollte im Contract stehen.
   - FR-09 verlangt Klartext zu verletzten Restriktionen. `verstoesse` ist aber nicht an den Status gekoppelt. Bei `optimal` müsste `verstoesse` leer sein oder fehlen, das ist nicht definiert.
   - Der Datenschutz-NFR (keine Personendaten im Log) betrifft `teilnehmer`. Das Schema sagt nichts dazu, ob Namen oder IDs verwendet werden. Das ist nicht festgelegt.
5. **Kleinere Inkonsistenzen.**
   - `verstoesse.items` hat kein `additionalProperties: false`, im Gegensatz zu den übrigen Objekten.
   - `seed` ist optional, FR-10 und das Determinismus-Kriterium sprechen aber für Pflicht oder zumindest Ausgabe des verwendeten Seeds.
   - Das Frontmatter hat `project: ""`.
   - Die Spec nennt "CON-XXXX" als Platzhalter, obwohl die IDs bereits vergeben sind (CON-0003 bis CON-0005). Die Zuordnung von CON-0003 zum Daten-Contract sollte explizit sein.
   - Die Spec-Notation `TST-XXXX` entspricht ebenfalls noch nicht den vergebenen IDs.
6. **Fehlende Negativtests.** Der Contract nennt keine Gegenbeispiele für leere `teilnehmer` (erlaubt?), doppelte Teilnehmer oder `anzahl_slots: 0`. Ob ein Termin ohne Teilnehmer gültig ist, ist offen. Die Spec verbietet leere Termine ("keine leeren Termine anlegen"), das Schema erlaubt sie aber über fehlendes `minItems` bei `teilnehmer`.
