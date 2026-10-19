"""Erzeugt Zeitslots aus Tagen, Zeitfenster und Slotlänge."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from itertools import pairwise

from konfiplaner.modell import ModellFehler, Zeitslot


def erzeuge_slots(tage: list[str], beginn: time, ende: time, laenge_min: int) -> list[Zeitslot]:
    """Je Tag lückenlose Slots der Länge `laenge_min` zwischen `beginn` und `ende`.

    Ein Rest, der kürzer als ein Slot ist, entfällt.
    """
    if laenge_min < 1:
        raise ModellFehler("Slotlänge muss mindestens 1 Minute sein")
    if ende <= beginn:
        raise ModellFehler("Ende liegt nicht nach dem Beginn")
    tage = [t.strip() for t in tage if t.strip()]
    if not tage:
        raise ModellFehler("Mindestens ein Tag nötig")
    if len(set(tage)) != len(tage):
        raise ModellFehler("Tage müssen eindeutig sein")
    d = date(2000, 1, 1)
    schritt = timedelta(minutes=laenge_min)
    grenze = datetime.combine(d, ende)
    slots = []
    for tag in tage:
        start = datetime.combine(d, beginn)
        while start + schritt <= grenze:
            slots.append(Zeitslot(tag, start.time(), (start + schritt).time()))
            start += schritt
    if not slots:
        raise ModellFehler("Das Zeitfenster ist kürzer als ein Slot")
    return slots


def raster_aus_fenstern(fenster: list[Zeitslot]) -> list[Zeitslot]:
    """Lückenloses Raster der von Zeitfenstern überdeckten Abschnitte (SPEC-0008 FR-03).

    Je Tag (in Reihenfolge des ersten Auftretens) bilden alle Anfangs- und Endzeiten die Grenzen;
    Abschnitte, die kein Fenster überdeckt, entfallen. Zwei Fenster überschneiden sich genau dann,
    wenn sie einen Abschnitt teilen, auch bei Teilüberlappung.
    """
    tage: dict[str, list[Zeitslot]] = {}
    for f in fenster:
        tage.setdefault(f.tag, []).append(f)
    raster = []
    for tag, fs in tage.items():
        grenzen = sorted({t for f in fs for t in (f.start, f.ende)})
        for a, b in pairwise(grenzen):
            if any(f.start <= a and b <= f.ende for f in fs):
                raster.append(Zeitslot(tag, a, b))
    return raster
