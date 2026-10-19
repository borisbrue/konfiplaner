---
id: SPEC-0011
title: "Visuelles Design im Dark Mode"
type: feature           # feature | bug-fix
status: implemented           # draft | review | approved | implemented | deprecated
owner: "Boris Brünen"
created: 2026-10-19
updated: 2026-10-19
version: 0.2.0
priority: medium        # low | medium | high | critical
tags: [design, dark-mode, gui, barrierefreiheit]
depends_on: ["SPEC-0005", "SPEC-0009", "SPEC-0010"]          # z.B. ["SPEC-0001"]
fr_test_map:
  FR-01: TST-0023
  FR-02: TST-0023
  FR-03: TST-0023
  FR-04: TST-0023
  FR-05: TST-0022
  FR-06: TST-0022
  FR-07: TST-0022
  FR-08: TST-0022
  FR-09: TST-0022
  FR-10: TST-0022
  FR-11: TST-0023
  FR-12: TST-0022
contracts: ["CON-0016"]           # z.B. ["CON-0001"] – MUSS mindestens einen Eintrag enthalten
tests: ["TST-0022", "TST-0023"]               # z.B. ["TST-0001"] – MUSS mindestens einen Eintrag enthalten
---

# Visuelles Design im Dark Mode

> **Status:** implemented · **Owner:** Boris Brünen · **Version:** 0.2.0

## 1. Kontext & Motivation

Die Oberfläche (SPEC-0005 ff.) ist funktional, sieht aber aus wie ein Standard-Formular. Wer täglich 100 Lehrkräfte und 26 Konferenzen sichtet, braucht eine Oberfläche, die schnell lesbar ist, Konflikte erkennen lässt und Freude macht. Das Design folgt dem Gegenstand: eine Schiefertafel bei Abendlicht, Kreide als Akzent, und jede Fachkonferenz hat ihre eigene Fachfarbe, wie auf einem Stundenplan.

## 2. Zielsetzung

**Primärziel:** Ein durchgängiges dunkles Design (Dark Mode zuerst) mit einer Seitenleiste für den Ablauf, lesbarer Schrift und Fachfarben, ohne Änderung der Funktionen.

**Erfolgskriterien (messbar):**
- [ ] Alle Text-/Flächen-Kombinationen erreichen mindestens 4,5:1 Kontrast (WCAG AA), Fachfarben auf Flächen mindestens 3:1.
- [ ] Alle bisherigen Abläufe und Tests bleiben unverändert gültig.
- [ ] Jede Konferenz hat in jeder Ansicht dieselbe Farbe.
- [ ] Bedienbar mit Tastatur, Fokus immer sichtbar, ab 1024×600.

**Nicht-Ziele (explizit):**
- Kein helles Design in dieser Version (die Token-Struktur erlaubt es später).
- Keine Animationen.
- Keine Funktionsänderungen.

## 3. User Stories

| ID    | Als ...   | möchte ich ...                                      | um ...                                       |
|-------|-----------|-----------------------------------------------------|----------------------------------------------|
| US-01 | Planer:in | Konferenzen an ihrer Farbe wiedererkennen           | lange Listen schnell zu überblicken          |
| US-02 | Planer:in | in der Seitenleiste sehen, wo ich im Ablauf bin     | nichts zu vergessen                          |
| US-03 | Planer:in | eine ruhige, lesbare Oberfläche bei dunkler Umgebung | lange damit zu arbeiten                      |

## 4. Funktionale Anforderungen

- **FR-01 (Tokens):** Farben, Radien, Abstände und Schriftgrößen sind als Design-Tokens an einer Stelle definiert; Stilregeln (QSS) und Palette werden daraus erzeugt.
- **FR-02 (Kontrast):** Text, gedämpfter Text, Akzent-Schaltflächen und Statusfarben erreichen auf ihren Flächen mindestens 4,5:1; Fachfarben als grafische Objekte mindestens 3:1.
- **FR-03 (Schrift):** Atkinson Hyperlegible Next (SIL OFL) ist gebündelt und wird beim Start geladen; fehlt sie, gilt die Systemschrift. Alle Größen stammen aus einer Skala.
- **FR-04 (Fachfarben):** Jede Konferenz hat eine stabile Farbe aus einer festen Palette von 36 Tönen (12 Farbtöne in drei Reihen, ohne das Gelb des Akzents). Die Farben werden den normalisierten Namen (SPEC-0007, so wie sie im Modell stehen) einer Datei nach Namen sortiert zugewiesen: dieselbe Datei ergibt immer dieselben Farben, es gibt bis 36 Konferenzen keine Doppelten, und eine Auswahl ändert nichts. Namen außerhalb der Datei bekommen eine stabile Farbe aus dem Namen. Zu dunkle Töne werden aufgehellt, bis sie als grafisches Objekt mindestens 3,2:1 erreichen. Sie erscheint als Punkt vor dem Namen in den Ansichten Konferenzen, Lehrkräfte, Ergebnis und Themen. Der Name steht immer daneben; Farbe ist nie der einzige Informationsträger.
- **FR-05 (Seitenleiste):** Die Schritte Daten, Konferenzen, Lehrkräfte, Regeln, Planen und Ergebnis stehen in einer Seitenleiste mit Nummer, Name und Kurzstatus (z. B. „101 Personen", „17 von 26 ausgewählt", „2 neu zu verplanen", „optimal"). Zustände: aktuell, abgeschlossen, gesperrt. Sie ersetzt die Tab-Leiste, die Seiten und Zustände bleiben dieselben.
- **FR-06 (Seitenkopf):** Jede Seite hat einen Titel und einen erklärenden Satz in Alltagssprache.
- **FR-07 (Fokus und Tastatur):** Jedes bedienbare Element zeigt einen sichtbaren Fokusring; die Seitenleiste ist mit Pfeiltasten und Strg+1 bis Strg+6 bedienbar.
- **FR-08 (Primäre Aktion):** Je Seite ist die Hauptaktion in der Akzentfarbe hervorgehoben (Datei öffnen, Planen, Exportieren); alle anderen Schaltflächen sind neutral.
- **FR-09 (Leere Zustände):** Fehlt Inhalt, nennt die Seite den nächsten Schritt (z. B. „Noch keine Datei. Excel-Datei öffnen oder hier ablegen.").
- **FR-10 (Ablegen):** Eine `.xlsx`-Datei, die auf das Fenster gezogen wird, wird geladen.
- **FR-11 (Statusfarben):** Konflikt (Koralle), Fehler (Rose), bestätigt (Mint) und Hinweis (Himmel) kommen immer mit Text; Statuszeilen der Tabellen nutzen sie.
- **FR-12 (Größe):** Die Oberfläche ist ab 1024×600 bedienbar: Seitenleiste und Seitenkopf bleiben stehen, Tabellen scrollen selbst. Aktionen stehen dort, wo sie wirken (Auswahlaktionen bei Suche und Filter, Planungsaktionen unten rechts).

## 5. Nicht-funktionale Anforderungen

| Kategorie     | Anforderung                                                       |
|---------------|-------------------------------------------------------------------|
| Accessibility | WCAG AA Kontrast, Fokus sichtbar, Tastaturbedienung               |
| Performance   | Start mit Design < 1 s zusätzlich, keine Zeichenverzögerung bei 100 Zeilen |
| Wartbarkeit   | Eine Quelle für Farben und Größen (`design.py`)                   |
| Lizenz        | Schrift unter SIL OFL, Lizenztext liegt bei                       |

## 6. Akzeptanzkriterien (Gherkin)

```gherkin
Feature: Design

  Scenario: Fachfarbe ist überall gleich
    Given die Konferenz "Deutsch" kommt in mehreren Ansichten vor
    Then hat sie überall dieselbe Farbe und ihren Namen daneben
```

## 7. Edge Cases & Fehlerfälle

- Zwei Konferenzen mit ähnlicher Farbe: der Name unterscheidet sie, die Palette hat 12 deutlich getrennte Töne.
- Schrift nicht ladbar: Systemschrift, keine Fehlermeldung.
- Sehr schmales Fenster: Inhalt scrollt, die Seitenleiste bleibt bedienbar.

## 8. Contracts (was wird garantiert)

| Contract-ID | Typ      | Was wird garantiert?                          |
|-------------|----------|-----------------------------------------------|
| CON-0016    | behavior | Sichtbares Verhalten des Designs              |

## 9. Tests (wie wird verifiziert)

| Test-ID  | Level      | Was prüft der Test?                                          |
|----------|------------|--------------------------------------------------------------|
| TST-0022 | acceptance | Gherkin aus CON-0016: Seitenleiste, Seitenkopf, Ablegen, Leere Zustände |
| TST-0023 | unit       | Tokens, Kontrastverhältnisse, Fachfarben, Stilregeln, Schrift |

## 10. Offene Fragen

- [ ] Helles Design als zweite Ausprägung (spätere Spec).

## 11. Änderungshistorie

| Datum      | Version | Autor        | Änderung            |
|------------|---------|--------------|---------------------|
| 2026-10-19 | 0.1.0   | Boris Brünen | Initiale Erstellung |
| 2026-10-19 | 0.2.0   | Boris Brünen | Umsetzung: Fachfarben-Zuweisung (36 Töne, Aufhellung), Aktionen nach Zweck gruppiert |
