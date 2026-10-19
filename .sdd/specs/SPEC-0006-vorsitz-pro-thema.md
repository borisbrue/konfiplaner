---
id: SPEC-0006
title: "Vorsitz pro Thema"
type: feature           # feature | bug-fix
status: implemented           # draft | review | approved | implemented | deprecated
owner: "Boris Brünen"
created: 2026-10-19
updated: 2026-10-19
version: 0.1.0
priority: high        # low | medium | high | critical
tags: [vorsitz, solver, import, export, gui]
depends_on: ["SPEC-0001", "SPEC-0002", "SPEC-0003", "SPEC-0004", "SPEC-0005"]          # z.B. ["SPEC-0001"]
fr_test_map:
  FR-01: TST-0013
  FR-02: TST-0012
  FR-03: TST-0012
  FR-04: TST-0012
  FR-05: TST-0012
  FR-06: TST-0013
  FR-07: TST-0013
  FR-08: TST-0013
  FR-09: TST-0012
contracts: ["CON-0011"]           # z.B. ["CON-0001"] – MUSS mindestens einen Eintrag enthalten
tests: ["TST-0012", "TST-0013"]               # z.B. ["TST-0001"] – MUSS mindestens einen Eintrag enthalten
---

# Vorsitz pro Thema

> **Status:** implemented · **Owner:** Boris Brünen · **Version:** 0.1.0

## 1. Kontext & Motivation

Ein Thema kann einen Vorsitz haben: eine Person, die den Termin leitet und deshalb zwingend im Termin sein muss. Der Vorsitz ist eine normale Person der Personenliste (kein Teilnehmer-Schwerpunkt nötig) und wirkt auf Modell, Solver, Import, Export und GUI.

## 2. Zielsetzung

**Primärziel:** Ist für ein Thema ein Vorsitz angegeben, nimmt diese Person an jedem stattfindenden Termin des Themas teil.

**Erfolgskriterien (messbar):**
- [ ] In jedem Plan mit Status `optimal` oder `machbar` steht der Vorsitz in allen Terminen seines Themas (Standardregel hart).
- [ ] Ist das nicht möglich (z. B. Vorsitz nicht verfügbar), nennt die Begründung die Regel `vorsitz` und das Thema.
- [ ] Der Vorsitz lässt sich im Excel-Import (Spalte `Vorsitz`) und in der GUI angeben und erscheint im Export.

**Nicht-Ziele (explizit):**
- Kein eigener Leitungs-Personenkreis außerhalb der Personenliste.
- Mehrere Vorsitzende pro Thema (später als eigene Spec).

## 3. User Stories

| ID    | Als ...   | möchte ich ...                                   | um ...                                       |
|-------|-----------|--------------------------------------------------|----------------------------------------------|
| US-01 | Planer:in | für ein Thema eine Person als Vorsitz festlegen  | dass sie zwingend im Termin ist              |
| US-02 | Planer:in | den Vorsitz im Plan und Export erkennen          | zu sehen, wer den Termin leitet              |

## 4. Funktionale Anforderungen

- **FR-01 (Modell):** `Thema` hat ein optionales Feld `vorsitz` (Name einer Person der Personenliste). Ein unbekannter Name ist ein Modellfehler. Pro Thema gibt es höchstens einen Vorsitz; eine Person darf mehrere Themen leiten.
- **FR-02 (Grundregel):** Neue Grundregel `vorsitz` (Standard hart): Der Vorsitz nimmt an jedem stattfindenden Termin seines Themas teil. Wie alle Grundregeln ist sie hart, weich oder aus konfigurierbar (SPEC-0003 FR-03); als weiche Regel kostet jeder Termin ohne Vorsitz das Gewicht.
- **FR-03 (Teilnahme ohne Schwerpunkt):** Der Vorsitz nimmt am Termin teil, auch wenn das Thema keiner seiner Schwerpunkte ist. Für Überschneidungen und Verfügbarkeiten gelten dieselben Regeln wie für jede Teilnahme.
- **FR-04 (Mindestanzahl):** Der Vorsitz zählt zur Mindestanzahl des Termins (SPEC-0002 FR-03).
- **FR-05 (Mehrere Termine):** Hat ein Thema mehrere Termine, ist der Vorsitz in allen; die Regel „höchstens ein Termin je Person und Thema" gilt für ihn nicht. Hat der Vorsitz das Thema als Schwerpunkt, genügt mindestens ein Termin für `schwerpunkte`.
- **FR-06 (Import):** Das Blatt `Themen` hat eine optionale Spalte `Vorsitz` (Überschriften auch `Vorsitzender`, `Leitung`). Ein Name, der nicht im Blatt `Personen` steht, ist ein Fehler mit Blatt, Zeile und Spalte. Eine leere Zelle bedeutet keinen Vorsitz.
- **FR-07 (Export):** Das Blatt `Termine` hat eine Spalte `Vorsitz`, das Blatt `Personen` eine Spalte `Rolle` (`Vorsitz` oder `Teilnahme`).
- **FR-08 (GUI):** Die Themen-Tabelle hat die Spalte `Vorsitz` mit Auswahl aus den Personen oder „keiner".
- **FR-09 (Diagnose):** Ist kein Plan möglich, weil der Vorsitz nicht kann, nennt die Begründung die Regel `vorsitz` und das Thema.

## 5. Nicht-funktionale Anforderungen

| Kategorie     | Anforderung                                                  |
|---------------|--------------------------------------------------------------|
| Performance   | Planungsdauer weiter ≤ 60 s für 500/30/40 (CON-0005)         |
| Datenschutz   | Keine Personennamen im Log                                   |
| Kompatibilität| Dateien ohne Spalte `Vorsitz` verhalten sich wie bisher      |

## 6. Akzeptanzkriterien (Gherkin)

```gherkin
Feature: Vorsitz

  Scenario: Vorsitz ist im Termin
    Given das Thema "Taufe" hat den Vorsitz "Frau Meier", die das Thema nicht als Schwerpunkt hat
    When ich plane
    Then ist "Frau Meier" Teilnehmerin jedes Termins von "Taufe"

  Scenario: Vorsitz nicht verfügbar
    Given der Vorsitz ist in keinem passenden Slot verfügbar
    When ich plane
    Then ist der Status "kein_plan" und die Begründung nennt "vorsitz" und das Thema
```

## 7. Edge Cases & Fehlerfälle

- Vorsitz hat zwei Themen, die sich zeitlich überschneiden würden → Termine verteilen sich auf verschiedene Slots.
- Person ist Vorsitz und Schwerpunkt desselben Themas → einmal in jedem Termin, kein Doppelzählen.
- Name im Vorsitz kommt in `Personen` doppelt vor → die erste Zeile gilt (SPEC-0001 FR-08).

## 8. Contracts (was wird garantiert)

| Contract-ID | Typ      | Was wird garantiert?                                          |
|-------------|----------|---------------------------------------------------------------|
| CON-0011    | behavior | Vorsitz in Planung, Import, Export und GUI                    |

Betroffene bestehende Artefakte (mit angepasst): `importmodell-und-fehlerliste.schema.json` (CON-0001, Feld `vorsitz`), `export-blattstruktur.schema.json` (CON-0008, Spalten `Vorsitz` und `Rolle`).

## 9. Tests (wie wird verifiziert)

| Test-ID  | Level      | Was prüft der Test?                                    |
|----------|------------|--------------------------------------------------------|
| TST-0012 | acceptance | Gherkin-Szenarien aus CON-0011 (Solver, Regel)         |
| TST-0013 | unit       | Modell, Import, Export, GUI-Tabelle                    |

## 10. Offene Fragen

- [ ] Mehrere Vorsitzende je Thema (bewusst nicht in v1).

## 11. Änderungshistorie

| Datum      | Version | Autor        | Änderung            |
|------------|---------|--------------|---------------------|
| 2026-10-19 | 0.1.0   | Boris Brünen | Initiale Erstellung |
| 2026-10-19 | +      | Boris Brünen | Nachtrag zu SPEC-0007 (0..n Schwerpunkte), Version unverändert |
