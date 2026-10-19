"""Hilfen zum Erzeugen von Test-Excel-Dateien."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook


def schreibe(pfad: Path, blaetter: dict[str, list[list]]) -> Path:
    mappe = Workbook()
    mappe.remove(mappe.active)
    for name, zeilen in blaetter.items():
        ws = mappe.create_sheet(name)
        for z in zeilen:
            ws.append(z)
    mappe.save(pfad)
    return pfad


PERSONEN = [["Name", "Thema 1", "Thema 2"], ["Anna", "Taufe", "Abendmahl"], ["Ben", "Abendmahl", "Taufe"]]
THEMEN = [["Name", "Wichtigkeit", "Mindestanzahl", "Dauer"], ["Taufe", 3, 2, 45], ["Abendmahl", 5, 2, 90]]
SLOTS = [
    ["Tag", "Start", "Ende"],
    ["Mo", "08:00", "08:45"],
    ["Mo", "08:45", "09:30"],
    ["Mo", "09:30", "10:15"],
]


# Lehrerliste (SPEC-0007) mit erfundenen Namen
LEHRER_KOPF = [
    "Nachname ",
    "Vorname ",
    "Fächer",
    "Fachkonferenz I ",
    "Fachkonferenz II",
    "ggfs. FK III (Absprache mit der Leitung)",
    "Vorsitzende ",
]
LEHRER = [
    ["Meier", "Anna", "D, E", "Deutsch", "Englisch", None, "Deutsch"],
    ["Schulz", "Ben", "E, M", "Englisch", "Mathematik", None, "Englisch"],
    ["Kaya", "Cem", "M", "Mathematik", None, None, "Mathematik"],
    ["Roth", "Dora", "Sp", "Sport", "Deutsch", None, "Sport"],
]


def lehrerliste(zeilen: list[list] | None = None, zeitslots: bool = True) -> dict[str, list[list]]:
    blaetter: dict[str, list[list]] = {"Tabelle1": [LEHRER_KOPF, *(LEHRER if zeilen is None else zeilen)]}
    if zeitslots:
        blaetter["Zeitslots"] = SLOTS
    return blaetter
