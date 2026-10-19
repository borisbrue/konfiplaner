---
id: SPEC-0001
title: "Excel-Import von Personen und Themen"
type: feature
status: implemented
owner: "Boris Brünen"
created: 2026-10-19
updated: 2026-10-19
version: 0.3.0
priority: high
tags: [import, excel]
depends_on: ["SPEC-0002"]
fr_test_map:
  FR-01: TST-0002
  FR-02: TST-0002
  FR-03: TST-0002
  FR-04: TST-0002
  FR-05: TST-0002
  FR-06: TST-0002
  FR-07: TST-0002
  FR-08: TST-0002
  FR-09: TST-0001
  FR-10: TST-0002
contracts: ["CON-0001", "CON-0002"]
tests: ["TST-0001", "TST-0002"]
---

# Excel-Import von Personen und Themen

> **Status:** implemented · **Owner:** Boris Brünen · **Version:** 0.3.0

## 1. Kontext & Motivation

KonfiPlaner stellt Personen zu Terminen zusammen. Die Eingangsdaten liegen bei den Anwendern bereits als Excel-Listen vor (Personen, Themen, Zeitslots, Verfügbarkeiten). Der Import liest diese Listen in das Domänenmodell (SPEC-0002) ein und meldet Datenfehler verständlich, statt still falsch zu planen.

## 2. Zielsetzung

**Primärziel:** Eine Excel-Datei (`.xlsx`) wird validiert und fehlerfrei in das Domänenmodell überführt.

**Erfolgskriterien (messbar):**
- [ ] Alle Datenfehler werden mit Blatt, Zeile und Spalte gemeldet (kein Abbruch beim ersten Fehler).
- [ ] Import von 500 Personen und 30 Themen dauert < 2 s.

**Nicht-Ziele (explizit):**
- Kein Schreiben/Ändern der Quelldatei.
- Keine Formate außer `.xlsx` (CSV/ODS später).

## 3. User Stories

| ID    | Als ...        | möchte ich ...                              | um ...                                   |
|-------|----------------|---------------------------------------------|------------------------------------------|
| US-01 | Planer:in      | meine bestehenden Excel-Listen laden        | Daten nicht neu eingeben zu müssen       |
| US-02 | Planer:in      | alle Datenfehler auf einmal sehen           | die Liste in einem Durchgang zu korrigieren |

## 4. Funktionale Anforderungen

- **FR-01:** Der Import liest das Blatt `Personen` (Pflicht) sowie `Themen`, `Zeitslots` und optional `Verfügbarkeiten`. Fehlen `Themen` oder `Zeitslots` in der Datei, werden diese Daten über die GUI (SPEC-0005) ergänzt.
- **FR-02:** `Personen` enthält je Zeile: Name, Thema 1, Thema 2 (beide Pflicht, verschieden). Das ist das Minimalformat der Beispieldatei.
- **FR-03:** `Themen` enthält je Zeile: Name (eindeutig), Wichtigkeit (ganzzahlig, 1 = unwichtig … 5 = sehr wichtig), Mindestanzahl, Dauer in Minuten.
- **FR-04:** `Zeitslots` enthält je Zeile: Tag, Start, Ende. `Verfügbarkeiten` hat je Zeile Person, Tag, Start und nennt die Slots, in denen die Person kann (Slot = Tag + Start); Personen ohne Zeile und ein fehlendes Blatt bedeuten „jederzeit verfügbar". Verfügbarkeiten setzen das Blatt `Zeitslots` voraus.
- **FR-05:** Das Themenset ergibt sich aus `Themen`; fehlt das Blatt, aus den in `Personen` genannten Themen (dann mit Standardwerten, in der GUI anpassbar). Unbekannte Themen bei vorhandenem Blatt `Themen` sind ein Fehler.
- **FR-06:** Spaltenüberschriften werden unabhängig von Groß-/Kleinschreibung und Leerzeichen erkannt; die Spaltenzuordnung ist konfigurierbar.
- **FR-07:** Der Import liefert eine Fehlerliste (Blatt, Zeile, Spalte, Meldung); bei mindestens einem Fehler wird kein Modell geliefert.
- **FR-10 (Zeilennummern):** Zeilennummern in Meldungen sind die Excel-Zeilen (Kopfzeile = 1).
- **FR-09 (Abhängigkeit):** Der Import erzeugt ausschließlich Objekte des Domänenmodells aus SPEC-0002 (Contract CON-0003) und kennt weder Solver noch GUI.
- **FR-08:** Doppelte Personen werden als Warnung gemeldet.

## 5. Nicht-funktionale Anforderungen

| Kategorie     | Anforderung                                                  |
|---------------|--------------------------------------------------------------|
| Performance   | 500 Personen / 30 Themen < 2 s                               |
| Datenschutz   | Personendaten bleiben lokal, keine Namen im Log              |
| Robustheit    | Beschädigte oder passwortgeschützte Dateien → klare Fehlermeldung |

## 6. Akzeptanzkriterien (Gherkin)

```gherkin
Feature: Excel-Import

  Scenario: Gültige Datei
    Given eine Excel-Datei mit gültigen Blättern Personen, Themen und Zeitslots
    When ich sie importiere
    Then erhalte ich ein Modell mit allen Personen, Themen und Slots

  Scenario: Unbekanntes Schwerpunktthema
    Given eine Person mit Schwerpunktthema "Abendmahl" ohne passende Zeile in Themen
    When ich importiere
    Then erhalte ich einen Fehler mit Blatt "Personen", Zeile und Spalte
    And es wird kein Modell geliefert

  Scenario: Zwei gleiche Schwerpunktthemen
    Given eine Person mit identischem Thema 1 und Thema 2
    When ich importiere
    Then erhalte ich einen Fehler für diese Zeile
```

## 7. Edge Cases & Fehlerfälle

- Leere Zeilen und Zeilen mit nur Leerzeichen werden ignoriert.
- Zeiten als Excel-Zeitwert oder als Text `HH:MM`.
- Zellen mit Formeln: der berechnete Wert zählt.
- Umlaute und Sonderzeichen in Namen bleiben unverändert.

## 8. Contracts (was wird garantiert)

| Contract-ID | Typ  | Was wird garantiert?                                   |
|-------------|------|--------------------------------------------------------|
| CON-0001    | data | JSON-Schema des Importergebnisses und der Fehlerliste  |
| CON-0002    | behavior | Gherkin-Szenarien zum Excel-Import                 |

## 9. Tests (wie wird verifiziert)

| Test-ID  | Level      | Was prüft der Test?                         |
|----------|------------|---------------------------------------------|
| TST-0001 | unit       | Schema des Importergebnisses                |
| TST-0002 | acceptance | Gherkin-Szenarien aus CON-0002              |
| TST-0002 | unit       | Zeit- und Spaltenerkennung                  |

## 10. Offene Fragen

- [ ] Beispieldatei folgt (Minimalformat: Name, Thema 1, Thema 2); Layout danach prüfen. Bis dahin gilt das Minimalformat plus Alias-Überschriften.
- [x] Fehlt das Blatt `Themen`, gelten Standardwerte (Wichtigkeit 3, Mindestanzahl 1, Dauer 45 min) und die GUI bietet die Bearbeitung an (Annahme, bis die Beispieldatei vorliegt).

## 11. Änderungshistorie

| Datum      | Version | Autor        | Änderung            |
|------------|---------|--------------|---------------------|
| 2026-10-19 | 0.1.0   | Boris Brünen | Initiale Erstellung |
| 2026-10-19 | 0.2.0   | Boris Brünen | Klärung: Mindestanzahl, Wichtigkeit, Excel-Layout, anpassbare Grundregeln |
| 2026-10-19 | 0.3.0   | Boris Brünen | SOLID-Review: Abhängigkeitsrichtung und Abstraktionen präzisiert |
