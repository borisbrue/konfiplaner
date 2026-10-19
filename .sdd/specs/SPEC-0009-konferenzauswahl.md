---
id: SPEC-0009
title: "Konferenzauswahl"
type: feature           # feature | bug-fix
status: implemented           # draft | review | approved | implemented | deprecated
owner: "Boris Brünen"
created: 2026-10-19
updated: 2026-10-19
version: 0.1.0
priority: high        # low | medium | high | critical
tags: [auswahl, konferenzen, gui]
depends_on: ["SPEC-0005", "SPEC-0007", "SPEC-0008"]          # z.B. ["SPEC-0001"]
fr_test_map:
  FR-01: TST-0019
  FR-02: TST-0019
  FR-03: TST-0019
  FR-04: TST-0019
  FR-05: TST-0019
  FR-06: TST-0019
  FR-07: TST-0018
  FR-08: TST-0019
  FR-09: TST-0019
contracts: ["CON-0014"]           # z.B. ["CON-0001"] – MUSS mindestens einen Eintrag enthalten
tests: ["TST-0018", "TST-0019"]               # z.B. ["TST-0001"] – MUSS mindestens einen Eintrag enthalten
---

# Konferenzauswahl

> **Status:** implemented · **Owner:** Boris Brünen · **Version:** 0.1.0

## 1. Kontext & Motivation

Die Liste enthält alle möglichen Fachkonferenzen. Für einen Planungslauf soll eine Auswahl davon stattfinden; die Lehrkräfte werden entsprechend zugeordnet. Wer durch die Auswahl eine Konferenz verliert, behält die übrigen seiner Konferenzen; wer keine mehr hat, wird für die manuelle Neuzuordnung (SPEC-0010) sichtbar gemacht.

## 2. Zielsetzung

**Primärziel:** Nur ausgewählte Konferenzen werden geplant; Personen und Vorsitz richten sich danach, und alle Folgen der Auswahl sind sichtbar.

**Erfolgskriterien (messbar):**
- [ ] Abgewählte Konferenzen erscheinen in keinem Termin, keiner Teilnehmerliste und keinem Verstoß.
- [ ] Die Rangfolge der übrigen Konferenzen einer Person bleibt erhalten und rückt nach.
- [ ] Personen, die durch die Auswahl keine Konferenz mehr haben, stehen in der Liste „Neu zuordnen" und im Export-Blatt „Hinweise".

**Nicht-Ziele (explizit):**
- Keine automatische Umverteilung (SPEC-0010: manuell).
- Kein Ändern der Quelldatei.

## 3. User Stories

| ID    | Als ...   | möchte ich ...                                       | um ...                                     |
|-------|-----------|------------------------------------------------------|--------------------------------------------|
| US-01 | Planer:in | aus allen Konferenzen eine Auswahl treffen           | nur die stattfindenden Konferenzen zu planen |
| US-02 | Planer:in | sehen, wer dadurch keine Konferenz mehr hat          | diese Lehrkräfte neu zuzuordnen            |

## 4. Funktionale Anforderungen

- **FR-01 (Auswahl):** Jede Konferenz ist ausgewählt oder abgewählt; Standard ist ausgewählt (auch für neu hinzukommende). Geplant werden nur ausgewählte Konferenzen.
- **FR-02 (Personen):** Eine abgewählte Konferenz entfällt aus den Konferenzen jeder Person (auch aus manuell zugeordneten, SPEC-0010 FR-01); die übrigen behalten ihre Reihenfolge (Rangfolge SPEC-0008 FR-05) und rücken nach.
- **FR-03 (Termine und Vorsitz):** Eine abgewählte Konferenz hat im Modell keine Termine und keinen Vorsitz; das Blatt `Konferenzen` bleibt unverändert, das abgeleitete Zeitraster ebenso.
- **FR-04 (Neu zuordnen):** Personen, die vor der Auswahl mindestens eine, danach keine Konferenz haben, stehen in der Liste „Neu zuordnen". Sie nehmen an keinem Termin teil. Personen, die schon in der Datei keine Konferenz hatten, bleiben in der Liste „Ohne Konferenz" (SPEC-0007 FR-09).
- **FR-05 (Planbarkeit):** Ohne mindestens eine ausgewählte Konferenz ist „Planen" nicht möglich.
- **FR-06 (Persistenz):** Die abgewählten Konferenzen werden gespeichert (Einstellungsspeicher) und beim nächsten Laden angewandt.
- **FR-07 (GUI):** Die Seite „Konferenzen" (zweiter Schritt) listet alle Konferenzen mit Häkchen, Mitgliederzahl, Vorsitz und Terminen, mit „Alle" und „Keine" und einem Zähler; darunter die Listen „Neu zuordnen" und „Ohne Konferenz".
- **FR-08 (Plan verwerfen):** Eine Änderung der Auswahl verwirft den vorhandenen Plan.
- **FR-09 (Hinweise):** Der Plan trägt für Personen aus „Neu zuordnen" die Warnung „<Name> hat durch die Auswahl keine Konferenz"; sie erscheint im Ergebnis und im Export-Blatt „Hinweise".

## 5. Nicht-funktionale Anforderungen

| Kategorie     | Anforderung                                             |
|---------------|---------------------------------------------------------|
| Performance   | Auswahländerung wirkt in < 100 ms (ohne Planung)        |
| Datenschutz   | Keine Namen im Log                                      |
| Kompatibilität| Ohne Abwahl verhält sich alles wie bisher               |

## 6. Akzeptanzkriterien (Gherkin)

```gherkin
Feature: Konferenzauswahl

  Scenario: Abgewählte Konferenz entfällt, Rest rückt nach
    Given eine Lehrkraft mit Fachkonferenz I "Deutsch" und II "Sport"
    When ich "Deutsch" abwähle
    Then ist "Sport" ihre erste Konferenz
    And "Deutsch" kommt im Plan nicht vor
```

## 7. Edge Cases & Fehlerfälle

- Die Auswahl entfernt den Vorsitz einer Konferenz nur aus dem Modell, nicht aus den Daten; Wiederauswahl stellt ihn her.
- Alle abgewählt → nicht planbar.
- Ein Name in den gespeicherten Abwahlen, den die Datei nicht kennt, wird ignoriert.

## 8. Contracts (was wird garantiert)

| Contract-ID | Typ      | Was wird garantiert?                              |
|-------------|----------|---------------------------------------------------|
| CON-0014    | behavior | Wirkung der Konferenzauswahl auf Modell, Plan, GUI |

## 9. Tests (wie wird verifiziert)

| Test-ID  | Level      | Was prüft der Test?                                        |
|----------|------------|------------------------------------------------------------|
| TST-0018 | acceptance | Gherkin aus CON-0014: Sitzung, Plan, GUI                   |
| TST-0019 | unit       | Auswahl, Nachrücken, Neu-zuordnen-Liste, Persistenz        |

## 10. Offene Fragen

- [ ] Soll die Auswahl auch Konferenzen ohne Termin (Blatt `Konferenzen`) sichtbar machen? (Annahme: ja, mit Termine = 0.)

## 11. Änderungshistorie

| Datum      | Version | Autor        | Änderung            |
|------------|---------|--------------|---------------------|
| 2026-10-19 | 0.1.0   | Boris Brünen | Initiale Erstellung |
| 2026-10-19 | +      | Boris Brünen | Nachtrag zu SPEC-0010 (Fixierungen, Lehrkräfte), Version unverändert |
