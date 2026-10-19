---
id: SPEC-0010
title: "Manuelle Zuordnung und Teilneuplanung"
type: feature           # feature | bug-fix
status: implemented           # draft | review | approved | implemented | deprecated
owner: "Boris Brünen"
created: 2026-10-19
updated: 2026-10-19
version: 0.1.0
priority: high        # low | medium | high | critical
tags: [lehrkraefte, teilneuplanung, fixierung]
depends_on: ["SPEC-0002", "SPEC-0003", "SPEC-0005", "SPEC-0006", "SPEC-0008", "SPEC-0009"]          # z.B. ["SPEC-0001"]
fr_test_map:
  FR-01: TST-0020
  FR-02: TST-0020
  FR-03: TST-0020
  FR-04: TST-0020
  FR-05: TST-0020
  FR-06: TST-0021
  FR-07: TST-0021
  FR-08: TST-0020
  FR-09: TST-0020
  FR-10: TST-0020
  FR-11: TST-0021
  FR-12: TST-0020
contracts: ["CON-0015"]           # z.B. ["CON-0001"] – MUSS mindestens einen Eintrag enthalten
tests: ["TST-0020", "TST-0021"]               # z.B. ["TST-0001"] – MUSS mindestens einen Eintrag enthalten
---

# Manuelle Zuordnung und Teilneuplanung

> **Status:** implemented · **Owner:** Boris Brünen · **Version:** 0.1.0

## 1. Kontext & Motivation

Nach der automatischen Zuordnung (SPEC-0007, SPEC-0009) will die Planerin Lehrkräfte selbst verteilen und ihre Parameter anpassen: Konferenzen und Rangfolge ändern (auch für mehrere Lehrkräfte gleichzeitig), Vorsitz wechseln, Termine sperren, eine Teilnahme fest vorgeben. Danach sollen nur die betroffenen Lehrkräfte neu verplant werden, während der Plan der übrigen unverändert bleibt.

## 2. Zielsetzung

**Primärziel:** Lehrkräfte lassen sich manuell zuordnen und parametrieren; nur die markierten Lehrkräfte werden neu verplant, alle anderen bleiben fest.

**Erfolgskriterien (messbar):**
- [ ] Nach einer Änderung an einer Lehrkraft ändert die Teilneuplanung die Teilnahme keiner anderen Lehrkraft.
- [ ] Eine fest vorgegebene Teilnahme bleibt in jedem Plan erhalten oder führt zu einer Begründung.
- [ ] Alle Änderungen sind pro Lehrkraft sichtbar und verwerfbar und überstehen ein Neuladen der Datei.

**Nicht-Ziele (explizit):**
- Kein Verschieben von Konferenzterminen (SPEC-0008).
- Keine automatische Umverteilung ohne Zutun.

## 3. User Stories

| ID    | Als ...   | möchte ich ...                                           | um ...                                          |
|-------|-----------|----------------------------------------------------------|-------------------------------------------------|
| US-01 | Planer:in | Konferenzen und Rangfolge einer Lehrkraft ändern         | Lücken nach der Auswahl zu schließen            |
| US-02 | Planer:in | bei mehreren Lehrkräften gleichzeitig Konferenzen vergeben | schnell viele Zuordnungen zu ändern             |
| US-03 | Planer:in | Vorsitz, gesperrte und feste Termine setzen              | Sonderfälle abzubilden                          |
| US-04 | Planer:in | nur geänderte Lehrkräfte neu verplanen                   | den übrigen Plan nicht anzufassen               |

## 4. Funktionale Anforderungen

- **FR-01 (Konferenzen und Rangfolge):** Für jede Lehrkraft lässt sich die geordnete Liste ihrer Konferenzen ersetzen (hinzufügen, entfernen, umsortieren). Die Änderung gilt vor der Konferenzauswahl (SPEC-0009), d. h. abgewählte Konferenzen entfallen weiterhin.
- **FR-02 (Sammeländerung):** Für mehrere Lehrkräfte gleichzeitig lässt sich eine Konferenz hinzufügen (am Ende oder an einer Position), entfernen oder die gesamte Liste ersetzen.
- **FR-03 (Vorsitz):** Der Vorsitz einer Konferenz lässt sich auf eine andere Person der Liste oder auf „keiner" ändern (SPEC-0006).
- **FR-04 (Nicht verfügbar):** Je Lehrkraft lassen sich einzelne Termine von Konferenzen mit Festterminen sperren; die Lehrkraft nimmt an gesperrten Terminen nicht teil (Regel `verfuegbarkeit`, SPEC-0003).
- **FR-05 (Fest teilnehmen):** Je Lehrkraft lässt sich die Teilnahme an einem Konferenztermin fest vorgeben (hart); sie bleibt in jedem Plan erhalten, sonst Begründung `fixierung` mit Person und Konferenz.
- **FR-06 (Fixierungen im Solver):** Der `Planer` nimmt optionale `Fixierungen` entgegen: für Personen die feste Teilnahme (ja/nein je Termin) und je Konferenz die festen Startslots. Fixierungen sind hart und nennen sich in Begründungen als Regel `fixierung`.
- **FR-07 (Markierung):** Jede Änderung markiert die betroffene Lehrkraft als „neu zu verplanen". Bei einem Vorsitzwechsel werden alter und neuer Vorsitz markiert. „Alles neu planen" löscht die Markierungen.
- **FR-08 (Teilneuplanung):** Die Teilneuplanung fixiert die Teilnahmen aller nicht markierten Lehrkräfte und alle Termine aus dem bisherigen Plan und plant nur die markierten neu (Rangfolge, Überschneidung, Vorsitz wie sonst). Gibt es keinen Plan, plant sie vollständig. Bei Erfolg ist die Markierung gelöscht.
- **FR-09 (Sichtbarkeit):** Pro Lehrkraft sind Konferenzen (Rangfolge), ursprüngliche Konferenzen, Vorsitz, gesperrte und feste Termine, Teilnahmen aus dem Plan sowie „geändert" und „neu zu verplanen" abrufbar. „Zurücksetzen" verwirft alle Änderungen einer Lehrkraft.
- **FR-10 (Persistenz):** Änderungen werden gespeichert und gelten nach dem Neuladen derselben Datei wieder; bei einer anderen Datei werden sie nicht angewandt. Unbekannte Namen werden ignoriert.
- **FR-11 (Teilneuplanung bei variablen Terminen):** Auch Konferenzen ohne Festtermine behalten bei der Teilneuplanung ihre bisherigen Startslots; die Anzahl möglicher Termine einer Konferenz wird nie unter die des bisherigen Plans gesenkt.
- **FR-12 (GUI):** Die Seite „Lehrkräfte" zeigt die Tabelle mit Filter, einen Dialog „Bearbeiten" (Konferenzen und Rangfolge, Vorsitz, Termine), einen Dialog „Sammeländerung" für mehrere markierte Zeilen, „Zurücksetzen", „Markierte neu verplanen" und „Alles neu planen".

## 5. Nicht-funktionale Anforderungen

| Kategorie     | Anforderung                                                   |
|---------------|---------------------------------------------------------------|
| Performance   | Teilneuplanung einzelner Lehrkräfte < 10 s bei 100/26         |
| Datenschutz   | Keine Namen im Log                                            |
| Nachvollziehbarkeit | Änderungen und Markierungen jederzeit einsehbar          |

## 6. Akzeptanzkriterien (Gherkin)

```gherkin
Feature: Manuelle Zuordnung und Teilneuplanung

  Scenario: Nur die markierte Lehrkraft ändert sich
    Given ein Plan und eine Lehrkraft, der ich eine andere Konferenz zuordne
    When ich die markierten Lehrkräfte neu verplane
    Then ist die Teilnahme aller anderen Lehrkräfte unverändert
```

## 7. Edge Cases & Fehlerfälle

- Die Teilneuplanung ist unlösbar (z. B. Mindestanzahl unterschritten): Begründung, Plan und Markierung bleiben unverändert.
- Eine Lehrkraft wird markiert und danach zurückgesetzt: die Markierung entfällt.
- Feste Teilnahme an zwei gleichzeitigen Terminen: keine Planung, Begründung nennt beide.
- Eine Konferenz wird nach der Änderung abgewählt: die Zuordnung bleibt gespeichert, wirkt aber nicht.

## 8. Contracts (was wird garantiert)

| Contract-ID | Typ      | Was wird garantiert?                                |
|-------------|----------|-----------------------------------------------------|
| CON-0015    | behavior | Manuelle Zuordnung, Fixierungen und Teilneuplanung  |

## 9. Tests (wie wird verifiziert)

| Test-ID  | Level      | Was prüft der Test?                                           |
|----------|------------|---------------------------------------------------------------|
| TST-0020 | acceptance | Gherkin aus CON-0015: Sitzung, Plan, GUI                      |
| TST-0021 | unit       | Fixierungen im Solver, Änderungen und Persistenz in der Sitzung |

## 10. Offene Fragen

- [ ] Soll die Teilneuplanung bei Unlösbarkeit automatisch weitere Lehrkräfte einbeziehen (z. B. alle der betroffenen Konferenz)? Annahme: nein, Begründung und manuelle Entscheidung.

## 11. Änderungshistorie

| Datum      | Version | Autor        | Änderung            |
|------------|---------|--------------|---------------------|
| 2026-10-19 | 0.1.0   | Boris Brünen | Initiale Erstellung |
