---
id: SPEC-0002
title: Domänenmodell und Planungs-Solver
type: feature
status: implemented
owner: Boris Brünen
created: 2026-10-19
updated: '2026-10-19'
version: 0.3.0
priority: high
tags:
- solver
- ortools
- core
depends_on:
- SPEC-0003
fr_test_map:
  FR-01: TST-0003
  FR-02: TST-0004
  FR-03: TST-0004
  FR-04: TST-0004
  FR-05: TST-0004
  FR-06: TST-0004
  FR-07: TST-0004
  FR-08: TST-0006
  FR-09: TST-0004
  FR-10: TST-0005
  FR-11: TST-0003
  FR-12: TST-0004
  FR-13: TST-0004
  FR-14: TST-0004
contracts:
- CON-0003
- CON-0004
- CON-0005
tests:
- TST-0003
- TST-0004
- TST-0005
started_at: '2026-10-19T13:12:27Z'
---
# Domänenmodell und Planungs-Solver

> **Status:** implemented · **Owner:** Boris Brünen · **Version:** 0.3.0

## 1. Kontext & Motivation

Kern von KonfiPlaner: aus Personen, Themen und Zeitslots einen Terminplan berechnen. Jede Person hat zwei Schwerpunktthemen (allgemein 0 bis n, SPEC-0007) aus einem festen Themenset. Jedes Thema muss mindestens einmal als Termin stattfinden; Themen unterscheiden sich in Wichtigkeit, Mindestanzahl und Dauer.

## 2. Zielsetzung

**Primärziel:** Ein Solver (Google OR-Tools CP-SAT) erzeugt einen Terminplan, der alle harten Restriktionen erfüllt und die weichen Ziele gewichtet optimiert.

**Erfolgskriterien (messbar):**
- [ ] Jedes Thema kommt in einem fertigen Plan mindestens als ein Termin vor.
- [ ] Kein Termin unterschreitet die Mindestanzahl seines Themas.
- [ ] Planung für 500 Personen / 30 Themen / 40 Slots liefert in ≤ 60 s eine Lösung (Zeitlimit konfigurierbar).
- [ ] Gleiche Eingabe + gleicher Seed → gleicher Plan (reproduzierbar).

**Nicht-Ziele (explizit):**
- Keine Ein-/Ausgabe (SPEC-0001, SPEC-0004) und keine GUI (SPEC-0005).
- Keine Online-/Echtzeit-Umplanung durch mehrere Nutzer.

## 3. User Stories

| ID    | Als ...   | möchte ich ...                                          | um ...                                      |
|-------|-----------|---------------------------------------------------------|---------------------------------------------|
| US-01 | Planer:in | dass jede Person in Terminen ihrer Schwerpunktthemen steht | niemand thematisch falsch eingeteilt wird |
| US-02 | Planer:in | dass wichtige Themen bevorzugt gut besetzt werden       | bei Engpässen die richtigen Prioritäten gelten |
| US-03 | Planer:in | eine Begründung, wenn kein gültiger Plan existiert      | die Eingabe gezielt anpassen zu können      |

## 4. Funktionale Anforderungen

- **FR-01 (Modell):** Domänenobjekte `Thema` (Name, Wichtigkeit, Mindestanzahl, Dauer), `Person` (Name, 0 bis n verschiedene, geordnete Schwerpunktthemen – das Minimalformat des Imports liefert genau 2, Lehrerlisten 0 bis 3 und mehr; SPEC-0007 FR-12, Verfügbarkeit), `Zeitslot`, `Termin` (Thema, Slot(s), Teilnehmer), `Plan`.
- **FR-02 (Themenabdeckung):** Jedes Thema findet statt. Es darf genau einen Termin je Thema geben; mehr sind möglich, aber nicht erforderlich. Kein Thema darf entfallen (hart, aber über SPEC-0003 anpassbar).
- **FR-03 (Mindestanzahl):** `Mindestanzahl` ist die Mindest-Teilnehmerzahl pro Termin (der Vorsitz zählt mit, SPEC-0006); jeder Termin des Themas erreicht sie (hart, anpassbar).
- **FR-14 (Auswahl, SPEC-0009):** Das Modell enthält nur die ausgewählten Themen; `themenabdeckung` bezieht sich auf diese. Abgewählte Themen sind nicht Teil des Modells.
- **FR-13 (Festtermine, SPEC-0008):** Ein `Thema` kann feste Termine (Zeitfenster) haben; dann findet es genau dort statt und der Solver wählt keine Startslots. Eine Person nimmt je Thema an höchstens einem Termin teil (der Vorsitz an allen).
- **FR-04 (Dauer):** Ein Termin belegt aufeinanderfolgende Slots, die mindestens die Themendauer abdecken. Der Startslot je Termin ist die zentrale Stellgröße des Solvers.
- **FR-05 (Schwerpunkte):** Jede Person wird mindestens einem Termin je Schwerpunktthema zugeordnet (hart, sofern verfügbar). Seit SPEC-0006 nimmt außerdem der Vorsitz eines Themas an dessen Terminen teil, auch ohne Schwerpunkt; er ist in jedem Termin des Themas, die Regel „höchstens ein Termin je Person und Thema" gilt für ihn nicht.
- **FR-06 (Keine Überschneidung):** Eine Person nimmt nie an zwei zeitlich überlappenden Terminen teil (hart).
- **FR-07 (Wichtigkeit):** Wichtigkeit ist ein Gewicht in der Zielfunktion. Bei Konflikten (z. B. überlappende Schwerpunkttermine einer Person) wird zuerst über die Zeitslots der Termine verhandelt: wichtige Themen bekommen bevorzugte Slots und möglichst vollständige Teilnahme, unwichtige Themen weichen aus. Ein Thema entfällt nie.
- **FR-08 (Restriktionen):** Alle Bedingungen werden über die Restriktions-Schnittstelle aus SPEC-0003 eingebunden, nicht fest im Solver verdrahtet.
- **FR-09 (Diagnose):** Ist kein Plan möglich, nennt der Solver die verletzten/kollidierenden Restriktionen in Klartext.
- **FR-11 (Abstraktion):** Der Solver steht hinter einer Schnittstelle `Planer` (Eingabe: Modell + Regelkonfiguration + Optionen, Ausgabe: `Plan`). CP-SAT ist eine austauschbare Implementierung; `Plan` ist solver-unabhängig und enthält Status, Termine, Verstöße und Begründungen.
- **FR-12 (Fortschritt/Abbruch):** `Planer` akzeptiert einen Fortschritts-Callback und ein Abbruchsignal und liefert bei Abbruch oder Zeitlimit die beste bisherige Lösung.
- **FR-10:** Zeitlimit, Seed und Gewichte sind konfigurierbar.

## 5. Nicht-funktionale Anforderungen

| Kategorie        | Anforderung                                                |
|------------------|------------------------------------------------------------|
| Performance      | ≤ 60 s für 500/30/40 (Standardhardware, Steam Deck genügt)  |
| Determinismus    | Gleicher Seed → gleicher Plan, garantiert nur mit 1 Solver-Worker und ohne wirksames Zeitlimit |
| Testbarkeit      | Solver ohne GUI/Excel aufrufbar (reine Library)            |
| Datenschutz      | Keine Personendaten im Log                                 |

## 6. Akzeptanzkriterien (Gherkin)

```gherkin
Feature: Planung

  Scenario: Einfacher Plan
    Given 3 Themen, 12 Personen mit je 2 Schwerpunkten und 6 Zeitslots
    When ich plane
    Then kommt jedes Thema mindestens einmal als Termin vor
    And jede Person ist in Terminen ihrer beiden Schwerpunktthemen

  Scenario: Mindestanzahl nicht erreichbar
    Given ein Thema mit Mindestanzahl 5 und nur 3 interessierten Personen
    When ich plane
    Then erhalte ich "kein Plan" mit Begründung zu diesem Thema

  Scenario: Wichtigkeit bei Engpass
    Given zwei Themen konkurrieren um denselben Slot
    When ich plane
    Then erhält das wichtigere Thema den besseren Slot
```

## 7. Edge Cases & Fehlerfälle

- Person ohne Verfügbarkeit → Warnung, nicht planbar für Schwerpunkt.
- Themendauer länger als jeder zusammenhängende Slot-Block.
- Zeitlimit erreicht → beste bisher gefundene Lösung mit Kennzeichen „nicht optimal".
- Mehr Slots/Räume als nötig → keine leeren Termine anlegen.

## 8. Contracts (was wird garantiert)

| Contract-ID | Typ      | Was wird garantiert?                                   |
|-------------|----------|--------------------------------------------------------|
| CON-0003    | data     | JSON-Schema Domänenmodell und Plan                     |
| CON-0004    | behavior | Gherkin-Szenarien zur Planung                          |
| CON-0005    | performance | SLO Planungsdauer                                   |

## 9. Tests (wie wird verifiziert)

| Test-ID  | Level       | Was prüft der Test?                              |
|----------|-------------|--------------------------------------------------|
| TST-0004 | acceptance  | Gherkin-Szenarien aus CON-0004                   |
| TST-0003 | unit        | Modellvalidierung (verschiedene Schwerpunkte, 0..n, …)      |
| TST-0005 | performance | 500/30/40 in ≤ 60 s                              |

## 10. Offene Fragen

- [x] Mindestanzahl = Teilnehmer pro Termin; ein Termin je Thema ist zulässig (geklärt 2026-10-19).
- [ ] (bewusst offen, nicht in v1) Höchstgröße pro Termin / Raumkapazität
- [x] Kein Thema darf entfallen; Wichtigkeit steuert Slot-Wahl und Gewichtung (geklärt).
- [ ] Dürfen Personen zum Erreichen der Mindestanzahl Termine außerhalb ihrer Schwerpunkte besuchen?
- [ ] (bewusst offen) Begrenzung paralleler Termine; v1 erlaubt sie unbegrenzt

## 11. Änderungshistorie

| Datum      | Version | Autor        | Änderung            |
|------------|---------|--------------|---------------------|
| 2026-10-19 | 0.1.0   | Boris Brünen | Initiale Erstellung |
| 2026-10-19 | 0.2.0   | Boris Brünen | Klärung: Mindestanzahl, Wichtigkeit, Excel-Layout, anpassbare Grundregeln |
| 2026-10-19 | 0.3.0   | Boris Brünen | SOLID-Review: Abhängigkeitsrichtung und Abstraktionen präzisiert |
| 2026-10-19 | +      | Boris Brünen | Nachtrag zu SPEC-0006 (Vorsitz), Version unverändert |
| 2026-10-19 | +      | Boris Brünen | Nachtrag zu SPEC-0007 (0..n Schwerpunkte), Version unverändert |
| 2026-10-19 | +      | Boris Brünen | Nachtrag zu SPEC-0008 (Festtermine, Rangfaktor), Version unverändert |
| 2026-10-19 | +      | Boris Brünen | Nachtrag zu SPEC-0009: Auswahl, Version unverändert |
