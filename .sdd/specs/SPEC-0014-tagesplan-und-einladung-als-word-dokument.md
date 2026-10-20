---
id: SPEC-0014
title: "Tagesplan und Einladung als Word-Dokument"
type: feature
status: approved
owner: "Boris Brünen"
created: 2026-10-20
updated: 2026-10-20
version: 0.1.0
priority: medium
tags: [tagesplan, einladung, word]
depends_on: ["SPEC-0005", "SPEC-0009"]
fr_test_map:
  FR-01: TST-0029
  FR-02: TST-0029
  FR-03: TST-0029
  FR-04: TST-0029
  FR-05: TST-0029
  FR-06: TST-0029
  FR-07: TST-0029
  FR-08: TST-0028
  FR-09: TST-0028
contracts: ["CON-0019"]
tests: ["TST-0028", "TST-0029"]
---

# Tagesplan und Einladung als Word-Dokument

> **Status:** draft · **Owner:** Boris Brünen · **Version:** 0.1.0

## 1. Kontext & Motivation

Zu einer schulinternen Fortbildung (SchiLF) gehört neben der Konferenzplanung der Ablauf des ganzen Tages: Begrüßung, Plenumsphase, Arbeit in den Fachkonferenzen, Pausen, Gruppenarbeit, Abschluss. Bisher wird die Einladung samt Ablaufplan von Hand in Word gesetzt, und die Liste der Fachkonferenzen muss dabei doppelt gepflegt werden. Die App kennt die gewählten Konferenzen bereits und soll das Einladungsdokument komplett erzeugen.

## 2. Zielsetzung

**Primärziel:** Den Tagesablauf in der App bearbeiten und daraus eine fertig gesetzte Einladung als `.docx` erzeugen.

**Erfolgskriterien (messbar):**
- [ ] Ein Tagesplan mit Kopf und Zeitblöcken lässt sich in der App bearbeiten und bleibt zwischen Sitzungen erhalten.
- [ ] Die gewählten Fachkonferenzen erscheinen automatisch im dafür markierten Block.
- [ ] Das Word-Dokument enthält Kopf, Ziele und die dreispaltige Ablauftabelle (Zeiten, Inhalt, Wer/Wie).

**Nicht-Ziele (explizit):**
- Keine automatische Bildung jahrgangsbezogener Gruppen oder Gruppenlisten.
- Kein PDF-Export und kein Übernehmen einer vorhandenen Word-Vorlage.
- Das Schullogo wird nicht mit der App oder im Repository ausgeliefert; es kann pro Rechner gewählt werden.

## 3. User Stories

| ID    | Als ...   | möchte ich ...                               | um ...                                          |
|-------|-----------|----------------------------------------------|-------------------------------------------------|
| US-01 | Planer:in | den Ablauf des Tages als Zeitblöcke bearbeiten | die Einladung nicht von Hand setzen zu müssen   |
| US-02 | Planer:in | dass die gewählten Fachkonferenzen automatisch im Ablauf stehen | sie nicht doppelt zu pflegen |
| US-03 | Planer:in | die Einladung als Word-Datei exportieren     | sie zu versenden und nachzubearbeiten           |

## 4. Funktionale Anforderungen

- **FR-01:** Ein Tagesplan besteht aus einem Kopf (Datum, Titel, Thema, Ziele als Liste, Arbeitsformen, Vorbereitung, Verschriftlichung) und geordneten Zeitblöcken. Ein Block hat Zeit (Beginn, optional Ende, Art `bereich`, `ab` oder `um`), Titel, Inhalt (mehrzeilig), „Wer/Wie“ und Art (`frei` oder `konferenzen`).
- **FR-02:** Ohne gespeicherten Plan gibt es einen neutralen Standardablauf (Stehkaffee, Begrüßung, Einstieg, Kaffeepause, Fachkonferenzen, Mittagspause, Gruppenarbeit, Austausch, Ende).
- **FR-03:** Zeiten werden als „8.30 – 8.40 Uhr“, „ab 8.00 Uhr“ und „15.00 Uhr“ ausgegeben (Stunde ohne führende Null, Minuten zweistellig, Punkt als Trenner). Die Konferenznamen stammen aus derselben Quelle wie im Excel-Export (SPEC-0004).
- **FR-04:** Ein Block der Art `konferenzen` trägt die Namen der ausgewählten Konferenzen (SPEC-0009), in der Reihenfolge der Konferenzliste, durch Komma getrennt vor seinem eigenen Inhalt ein. Abgewählte Konferenzen erscheinen nicht. Die Auswahl wird ausschließlich in SPEC-0009 verwaltet; der Tagesplan hat keine eigene.
- **FR-05:** Die Prüfung meldet je Block ein Ende, das nicht nach dem Beginn liegt (Fehler), und überlappende Blöcke (Warnung). Fehler verhindern den Export, Warnungen nicht.
- **FR-06:** Der Export erzeugt ein A4-Dokument im Querformat: Titelzeile „Wochentag, TT.MM.JJJJ: Titel“, „THEMA: …“, die Abschnitte Ziele/Inhalte (Aufzählung), Arbeitsformen, Vorbereitung und Verschriftlichung (leere Abschnitte entfallen), die Überschrift „Ablaufplan TT.MM.JJJJ“ und die Tabelle mit den Spalten „Zeiten“, „Inhalt“ und „Wer/Wie?“ (grauer Kopf). Der Blocktitel steht fett als erste Zeile der Inhaltsspalte.
- **FR-07:** Tagesplan und Logo-Pfad werden in den Einstellungen gespeichert, unabhängig von der geladenen Excel-Datei, in derselben Einstellungsdatei wie alle übrigen Einstellungen (SPEC-0005 FR-07), ohne zweite Ablage.
- **FR-08:** Die Seite „Einladung“ (siebter Schritt der Seitenleiste, verfügbar sobald eine Datei geladen ist) bearbeitet den Kopf und die Blöcke (hinzufügen, löschen, nach oben/unten) und exportiert. Eine vorhandene Zieldatei wird nur nach Bestätigung überschrieben.
- **FR-09:** Optional wird ein Logo (PNG oder JPG) oben rechts eingefügt; fehlt die Datei, wird ohne Logo exportiert.

## 5. Nicht-funktionale Anforderungen

| Kategorie     | Anforderung                                             |
|---------------|---------------------------------------------------------|
| Kompatibilität| Öffnet in Word und LibreOffice                          |
| Datenschutz   | Keine personenbezogenen Daten im Dokument; Logo nicht im Repository |

## 6. Akzeptanzkriterien (Gherkin)

Siehe `.sdd/contracts/behavior/tagesplan-und-einladung-verhalten.feature` (CON-0019).

## 7. Edge Cases & Fehlerfälle

- Datum fehlt → Titelzeile ohne Datum, Tabellenüberschrift „Ablaufplan“.
- Keine Konferenz ausgewählt → Block `konferenzen` zeigt nur seinen eigenen Inhalt.
- Logo-Datei fehlt oder ist unlesbar → Export ohne Logo, Hinweis in der Statusleiste.
- Zieldatei gesperrt → klare Fehlermeldung.

## 8. Contracts (was wird garantiert)

| Contract-ID | Typ  | Was wird garantiert?                                   |
|-------------|------|--------------------------------------------------------|
| CON-0019    | behavior | Tagesplan bearbeiten und als Einladung exportieren |

## 9. Tests (wie wird verifiziert)

| Test-ID  | Level      | Was prüft der Test?                                  |
|----------|------------|------------------------------------------------------|
| TST-0028 | acceptance | Seite „Einladung“ und Export (GUI)                   |
| TST-0029 | unit       | Modell, Zeitformat, Prüfung, Persistenz, Word-Inhalt |

## 10. Offene Fragen

- [ ] Jahrgangsbezogene Gruppen (5/6, 7/8, 9/10) automatisch bilden?

## 11. Änderungshistorie

| Datum      | Version | Autor        | Änderung            |
|------------|---------|--------------|---------------------|
| 2026-10-20 | 0.1.0   | Boris Brünen | Initiale Erstellung |
