---
id: SPEC-0015
title: "Update-Hinweis in der App"
type: feature
status: approved
owner: "Boris Brünen"
created: 2026-10-20
updated: 2026-10-20
version: 0.1.0
priority: medium
tags: [update, release, github]
depends_on: ["SPEC-0005", "SPEC-0011"]
fr_test_map:
  FR-01: TST-0031
  FR-02: TST-0030
  FR-03: TST-0031
  FR-04: TST-0030
  FR-05: TST-0030
  FR-06: TST-0031
  FR-07: TST-0031
contracts: ["CON-0020"]
tests: ["TST-0030", "TST-0031"]
---

# Update-Hinweis in der App

> **Status:** draft · **Owner:** Boris Brünen · **Version:** 0.1.0

## 1. Kontext & Motivation

KonfiPlaner wird als macOS-App an Kolleg:innen weitergegeben (GitHub-Release, SPEC-0014 und Folgende). Wer eine Version hat, erfährt bisher nicht, dass es eine neuere gibt, etwa nach einer Fehlerbehebung. Die App soll einen Hinweis zeigen, wenn im öffentlichen Release des Projekts eine neuere Version liegt.

## 2. Zielsetzung

**Primärziel:** Die App meldet unaufdringlich, dass eine neuere Version verfügbar ist, und führt zur Release-Seite.

**Erfolgskriterien (messbar):**
- [ ] Liegt im Release eine höhere Version, erscheint nach dem Start ein Hinweis mit Versionsnummer und Link.
- [ ] Ohne Verbindung oder bei Fehlern bleibt die App unverändert bedienbar, es erscheint kein Fehlerdialog.
- [ ] Der Hinweis lässt sich je Version ausblenden und die Prüfung abschalten.

**Nicht-Ziele (explizit):**
- Kein automatisches Herunterladen oder Ersetzen der App (mögliche spätere Stufe).
- Keine Übertragung von Nutzer- oder Plandaten; keine Statistik.
- Kein Erzeugen der Releases (Build-Workflow, getrennt davon).

## 3. User Stories

| ID    | Als ...       | möchte ich ...                              | um ...                                      |
|-------|---------------|---------------------------------------------|---------------------------------------------|
| US-01 | Nutzer:in     | informiert werden, wenn es eine neue Version gibt | Fehlerbehebungen nicht zu verpassen   |
| US-02 | Nutzer:in     | den Hinweis ausblenden oder abschalten      | nicht gestört zu werden                     |
| US-03 | Nutzer:in     | selbst nach Updates suchen                  | den Stand jederzeit zu prüfen               |

## 4. Funktionale Anforderungen

- **FR-01:** Die App kennt ihre Versionsnummer aus einer einzigen Quelle (`pyproject.toml`), auch im gebauten Paket, und zeigt sie unten in der Seitenleiste an (Design-Tokens, Kontrast und Tastaturbedienung nach SPEC-0011).
- **FR-02:** Beim Start fragt die App im Hintergrund (nicht blockierend, im selben Muster wie die Planung in SPEC-0005: eigener Thread, Ergebnis per Signal) die neueste stabile Version des Projekt-Releases ab (GitHub-Releases-Schnittstelle des Repositorys `borisbrue/konfiplaner`, ohne Anmeldung, Zeitlimit 5 s).
- **FR-03:** Versionen werden numerisch verglichen (`v0.2.0` > `0.1.9`, `0.10.0` > `0.9.0`; ein führendes `v` wird ignoriert). Nur eine höhere Version wird gemeldet; Vorabversionen, Entwürfe und unlesbare Tags werden ignoriert.
- **FR-04:** Der Hinweis erscheint als Karte unten in der Seitenleiste: „Version X verfügbar“ mit „Ansehen“ (öffnet die Release-Seite im Browser) und „Später“ (blendet den Hinweis für diese Version aus; spätere Versionen werden wieder gemeldet).
- **FR-05:** Menü „Datei → Nach Updates suchen…“ prüft sofort und meldet ausdrücklich das Ergebnis (neuere Version, „aktuell“ oder „Keine Verbindung“). Eine ausgeblendete Version wird dabei wieder gezeigt.
- **FR-06:** Schlägt die Abfrage fehl (keine Verbindung, Zeitüberschreitung, ungültige Antwort), ist das beim automatischen Start-Check still (nur Logeintrag) und beim manuellen Check eine kurze Meldung in der Statusleiste. Die App sendet dabei nur eine anonyme Abfrage mit dem Programmnamen und der Versionsnummer im User-Agent, keine Daten aus der App.
- **FR-07:** Der Start-Check läuft höchstens einmal in 24 Stunden und lässt sich über die Einstellung `update_pruefung` abschalten. Zeitpunkt der letzten Prüfung und ausgeblendete Version stehen in der Einstellungsdatei (SPEC-0005 FR-07).

## 5. Nicht-funktionale Anforderungen

| Kategorie     | Anforderung                                                   |
|---------------|---------------------------------------------------------------|
| Robustheit    | Netzwerkfehler dürfen das Fenster weder blockieren noch beenden |
| Datenschutz   | Nur anonyme Abfrage, keine Plan- oder Personendaten           |
| Testbarkeit   | Die Quelle der Release-Information ist austauschbar (kein Netz in Tests) |

## 6. Akzeptanzkriterien (Gherkin)

Siehe `.sdd/contracts/behavior/update-hinweis-verhalten.feature` (CON-0020).

## 7. Edge Cases & Fehlerfälle

- Kein Release vorhanden (404) oder Tag ohne Versionsnummer → kein Hinweis.
- Antwort nicht lesbar → wie Verbindungsfehler.
- Neue Version erscheint, während „Später“ für eine ältere gesetzt ist → Hinweis erscheint.
- Fenster wird vor dem Ende der Abfrage geschlossen → Abfrage wird verworfen, kein Absturz.
- App läuft aus dem Quelltext (Entwicklung, ohne installierte Version) → Version „0.0.0“, Prüfung bleibt möglich.

## 8. Contracts (was wird garantiert)

| Contract-ID | Typ      | Was wird garantiert?                          |
|-------------|----------|-----------------------------------------------|
| CON-0020    | behavior | Update-Hinweis, manuelle Prüfung, Ausblenden  |

## 9. Tests (wie wird verifiziert)

| Test-ID  | Level      | Was prüft der Test?                                        |
|----------|------------|------------------------------------------------------------|
| TST-0030 | acceptance | Hinweiskarte, „Später“, manuelle Prüfung (GUI, ohne Netz)  |
| TST-0031 | unit       | Version, Vergleich, Antwort lesen, Takt und Einstellungen  |

## 10. Offene Fragen

- [ ] Soll eine spätere Stufe die neue Version selbst herunterladen und die App ersetzen?
- [ ] Der Build-Workflow soll bei einem Versions-Tag das Release mit beiden Zips selbst anlegen (eigener Schritt, nicht Teil dieser Spec).

## 11. Änderungshistorie

| Datum      | Version | Autor        | Änderung            |
|------------|---------|--------------|---------------------|
| 2026-10-20 | 0.1.0   | Boris Brünen | Initiale Erstellung |
