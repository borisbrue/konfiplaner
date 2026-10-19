---
id: SPEC-0004
title: "Excel-Export des Terminplans"
type: feature
status: draft
owner: "Boris Brünen"
created: 2026-10-19
updated: 2026-10-19
version: 0.1.0
priority: medium
tags: [export, excel]
depends_on: ["SPEC-0002"]
contracts: []
tests: []
---

# Excel-Export des Terminplans

> **Status:** draft · **Owner:** Boris Brünen · **Version:** 0.1.0

## 1. Kontext & Motivation

Der berechnete Plan muss weitergegeben werden. Da die Eingaben in Excel vorliegen, ist Excel auch das natürliche Ausgabeformat.

## 2. Zielsetzung

**Primärziel:** Ein Plan wird als lesbare `.xlsx`-Datei exportiert.

**Erfolgskriterien (messbar):**
- [ ] Export enthält je Termin Thema, Zeit, Dauer und alle Teilnehmenden.
- [ ] Jede Person findet ihre Termine in einer Personen-Ansicht.

**Nicht-Ziele (explizit):**
- Kein PDF/Kalender-Export (ICS ggf. später).

## 3. User Stories

| ID    | Als ...   | möchte ich ...                       | um ...                              |
|-------|-----------|--------------------------------------|-------------------------------------|
| US-01 | Planer:in | den Plan als Excel speichern         | ihn zu verteilen und zu drucken     |
| US-02 | Teilnehmer:in | meine Termine gebündelt sehen    | zu wissen, wann ich wo sein muss    |

## 4. Funktionale Anforderungen

- **FR-01:** Blatt `Termine`: eine Zeile je Termin (Tag, Start, Ende, Thema, Teilnehmerzahl).
- **FR-02:** Blatt `Personen`: je Person ihre Termine in zeitlicher Reihenfolge.
- **FR-03:** Blatt `Themen`: Auslastung je Thema gegenüber Mindestanzahl, Kennzeichnung von Wichtigkeit.
- **FR-04:** Blatt `Hinweise`: Warnungen, verletzte weiche Restriktionen, Kennzeichen „nicht optimal".
- **FR-05:** Existierende Zieldatei wird nur nach Bestätigung überschrieben.

## 5. Nicht-funktionale Anforderungen

| Kategorie     | Anforderung                                      |
|---------------|--------------------------------------------------|
| Kompatibilität| Öffnet in Excel und LibreOffice                  |
| Performance   | 500 Personen < 3 s                               |

## 6. Akzeptanzkriterien (Gherkin)

```gherkin
Feature: Export

  Scenario: Plan exportieren
    Given ein fertiger Plan
    When ich nach "plan.xlsx" exportiere
    Then enthält die Datei die Blätter Termine, Personen, Themen und Hinweise
    And jede Person erscheint mit allen ihren Terminen
```

## 7. Edge Cases & Fehlerfälle

- Zieldatei in Excel geöffnet/gesperrt → klare Fehlermeldung.
- Plan „nicht optimal" → Hinweisblatt füllen.

## 8. Contracts (was wird garantiert)

| Contract-ID | Typ  | Was wird garantiert?                 |
|-------------|------|--------------------------------------|
| CON-XXXX    | data | Blatt- und Spaltenstruktur des Exports |

## 9. Tests (wie wird verifiziert)

| Test-ID  | Level      | Was prüft der Test?                   |
|----------|------------|---------------------------------------|
| TST-XXXX | contract   | Blattstruktur                         |
| TST-XXXX | acceptance | Gherkin aus Sektion 6                 |

## 10. Offene Fragen

- [ ] Gewünschtes Layout (z. B. Aushang pro Termin)?

## 11. Änderungshistorie

| Datum      | Version | Autor        | Änderung            |
|------------|---------|--------------|---------------------|
| 2026-10-19 | 0.1.0   | Boris Brünen | Initiale Erstellung |
