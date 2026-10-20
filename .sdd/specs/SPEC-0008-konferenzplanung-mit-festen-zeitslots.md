---
id: SPEC-0008
title: "Konferenzplanung mit festen Zeitslots"
type: feature           # feature | bug-fix
status: implemented           # draft | review | approved | implemented | deprecated
owner: "Boris Brünen"
created: 2026-10-19
updated: 2026-10-19
version: 0.1.0
priority: high        # low | medium | high | critical
tags: [konferenzen, zeitslots, rangfolge]
depends_on: ["SPEC-0001", "SPEC-0002", "SPEC-0003", "SPEC-0005", "SPEC-0007"]          # z.B. ["SPEC-0001"]
fr_test_map:
  FR-01: TST-0016
  FR-02: TST-0017
  FR-03: TST-0017
  FR-04: TST-0017
  FR-05: TST-0017
  FR-06: TST-0016
  FR-07: TST-0016
  FR-08: TST-0016
  FR-09: TST-0016
  FR-10: TST-0016
  FR-11: TST-0016
contracts: ["CON-0013"]           # z.B. ["CON-0001"] – MUSS mindestens einen Eintrag enthalten
tests: ["TST-0016", "TST-0017"]               # z.B. ["TST-0001"] – MUSS mindestens einen Eintrag enthalten
---

# Konferenzplanung mit festen Zeitslots

> **Status:** implemented · **Owner:** Boris Brünen · **Version:** 0.1.0

## 1. Kontext & Motivation

Bei Fachkonferenzen legt die Schule die Termine fest; viele Konferenzen finden gleichzeitig statt. Eine Lehrkraft kann dann nur an einer teilnehmen, außer ihre Konferenzen liegen zeitlich getrennt. Die Zeitslots gehören deshalb zur Konferenz und stehen in einem Excel-Blatt. Der Plan beantwortet: Wer nimmt an welcher Konferenz teil, wo kollidieren Konferenzen einer Person, und ist der Vorsitz frei?

## 2. Zielsetzung

**Primärziel:** Konferenzen haben feste Termine aus einem Excel-Blatt; bei Überschneidungen entscheidet die Rangfolge der Konferenzen einer Person (Fachkonferenz I vor II vor III), und alle Konflikte sind sichtbar.

**Erfolgskriterien (messbar):**
- [ ] Mit dem Blatt `Konferenzen` ist eine Lehrerliste ohne weitere Zeitangaben planbar.
- [ ] Überlappen zwei Konferenzen einer Person, nimmt sie an der höher eingestuften teil; die entgangene Teilnahme steht als Verstoß im Plan.
- [ ] Planung für 100 Personen und 26 Konferenzen in ≤ 60 s.

**Nicht-Ziele (explizit):**
- Der Solver wählt keine Zeiten für Konferenzen mit festem Termin.
- Keine automatische Mitgliedschaft in der Hauptkonferenz; Haupt-/Unterkonferenzfälle werden einzeln geklärt.

## 3. User Stories

| ID    | Als ...   | möchte ich ...                                          | um ...                                          |
|-------|-----------|---------------------------------------------------------|-------------------------------------------------|
| US-01 | Planer:in | die Termine je Konferenz in Excel vorgeben              | ohne Zeitraster-Formular zu planen              |
| US-02 | Planer:in | bei gleichzeitigen Konferenzen die Rangfolge gelten lassen | dass die wichtigere Konferenz der Lehrkraft vorgeht |
| US-03 | Planer:in | alle Kollisionen sehen                                  | Termine bei Bedarf zu verschieben               |

## 4. Funktionale Anforderungen

- **FR-01 (Blatt):** Das Blatt `Konferenzen` hat je Zeile eine Konferenz mit Tag, Start und Ende; optional Hauptkonferenz, Wichtigkeit und Mindestanzahl. Der Konferenzname wird wie in SPEC-0007 normalisiert (Status `sicher` nötig). Mehrere Zeilen derselben Konferenz sind mehrere feste Termine. Wichtigkeit, Mindestanzahl und Hauptkonferenz müssen je Konferenz übereinstimmen, sonst Fehler (Blatt, Zeile, Spalte).
- **FR-02 (Modell):** `Thema` hat optional `festtermine` (Zeitfenster Tag/Start/Ende). Ein Thema mit Festterminen findet in genau diesen Fenstern statt; der Solver verschiebt nichts. Die Dauer ergibt sich aus dem Fenster.
- **FR-03 (Zeitraster):** Aus den Zeitfenstern aller Konferenzen entsteht je Tag ein lückenloses Raster der überdeckten Abschnitte (Grenzen = alle Anfangs-/Endzeiten). Zwei Termine überschneiden sich genau dann, wenn sie einen Abschnitt teilen; Teilüberlappungen werden dadurch erfasst. Das Blatt `Zeitslots` und das Zeitraster-Formular entfallen für Konferenzen mit Festterminen.
- **FR-04 (Solver):** Jeder feste Termin findet statt (kein Kandidat entfällt, `themenabdeckung` gilt je Termin). Eine Person nimmt je Konferenz an höchstens einem Termin teil (der Vorsitz an allen, SPEC-0006).
- **FR-05 (Rangfolge):** Konflikte (Überschneidungen) löst die Regel `schwerpunkte`, wenn sie weich ist: Eine entgangene Teilnahme kostet Gewicht × Rangfaktor mit 100 für die erste, 10 für die zweite und 1 für weitere Konferenzen der Person. Dazu nimmt `Planungskontext.bedingung` einen optionalen `faktor` entgegen (SPEC-0003 FR-07).
- **FR-06 (Voreinstellung):** Für Lehrerlisten gilt das Profil „Verteilen" (SPEC-0012 FR-01) und löst dieses Profil ab. Für andere Dateien gilt: Enthält die Datei Konferenztermine, ist `schwerpunkte` standardmäßig weich, solange die Nutzerin die Regel nicht selbst gesetzt hat. Gespeichert werden nur von Hand gesetzte Regeln.
- **FR-07 (Konflikte sichtbar):** Jede entgangene Teilnahme steht als Verstoß mit Person und Konferenz im Plan, im Ergebnis (GUI) und im Export-Blatt „Hinweise".
- **FR-08 (Hauptkonferenz):** Die Spalte `Hauptkonferenz` verknüpft eine Unterkonferenz mit ihrer Hauptkonferenz. Beginnt ein Termin der Unterkonferenz nicht nach dem Ende aller Termine der Hauptkonferenz, ist das eine Warnung. Weitere Wirkung gibt es nicht (offene Frage).
- **FR-09 (Vorsitz):** Ist der Vorsitz zeitgleich in zwei Konferenzen eingetragen, gibt es keinen Plan mit harter Regel `vorsitz` und eine Begründung, die beide Konferenzen nennt (SPEC-0006 FR-09).
- **FR-10 (Fehler im Blatt):** Ungültige Zeiten (Ende ≤ Start), unbekannte oder nicht bestätigte Konferenznamen, Konferenzen der Lehrerliste ohne Termin im Blatt `Konferenzen` und Termine, die sich innerhalb derselben Konferenz überschneiden, sind Fehler mit Blatt, Zeile und Spalte.
- **FR-11 (GUI und Export):** Die Seite „Daten" zeigt die Termine je Konferenz (Reiter „Termine"); das Zeitraster-Formular ist bei Festterminen abgeschaltet. Das Ergebnis zeigt die Kollisionen als Hinweise.

## 5. Nicht-funktionale Anforderungen

| Kategorie     | Anforderung                                                    |
|---------------|----------------------------------------------------------------|
| Performance   | 100 Personen / 26 Konferenzen ≤ 60 s (CON-0005 bleibt gültig)   |
| Datenschutz   | Keine Namen im Log                                             |
| Kompatibilität| Dateien ohne Blatt `Konferenzen` verhalten sich wie bisher     |

## 6. Akzeptanzkriterien (Gherkin)

```gherkin
Feature: Konferenzplanung

  Scenario: Gleichzeitige Konferenzen, Rangfolge entscheidet
    Given eine Lehrkraft mit Fachkonferenz I "Deutsch" und II "Sport", beide am selben Termin
    When ich plane
    Then nimmt sie an "Deutsch" teil
    And der Plan nennt als Verstoß die entgangene Teilnahme an "Sport"
```

## 7. Edge Cases & Fehlerfälle

- Teilüberlappung (14:00–15:30 und 15:00–16:00) zählt als Überschneidung.
- Eine Konferenz mit zwei Terminen: die Person nimmt an einem teil, der Vorsitz an beiden.
- Fester Termin, zu dem niemand kann: Mindestanzahl nicht erreicht → Begründung.

## 8. Contracts (was wird garantiert)

| Contract-ID | Typ      | Was wird garantiert?                                     |
|-------------|----------|----------------------------------------------------------|
| CON-0013    | behavior | Konferenzplanung mit festen Terminen, Rangfolge, Konflikten |

## 9. Tests (wie wird verifiziert)

| Test-ID  | Level      | Was prüft der Test?                                         |
|----------|------------|-------------------------------------------------------------|
| TST-0016 | acceptance | Gherkin aus CON-0013: Import, Planung, Sitzung, GUI         |
| TST-0017 | unit       | Festtermine im Modell, Zeitraster-Ableitung, Solver, Rangfaktor |

## 10. Offene Fragen

- [ ] Haupt-/Unterkonferenz (GL → Sowi/WiPo, NW → Biologie/Physik): Folgt aus der Mitgliedschaft in einer Unterkonferenz die Mitgliedschaft in der Hauptkonferenz? Die Fälle werden einzeln mit der Fachseite geklärt.
- [ ] Verhalten bei zwei Terminen derselben Konferenz: nimmt jede Person an einem beliebigen teil oder ist die Zuordnung vorgegeben?

## 11. Änderungshistorie

| Datum      | Version | Autor        | Änderung            |
|------------|---------|--------------|---------------------|
| 2026-10-19 | 0.1.0   | Boris Brünen | Initiale Erstellung |
| 2026-10-20 | +      | Boris Brünen | Nachtrag zu SPEC-0012 (Verteilen), Version unverändert |
