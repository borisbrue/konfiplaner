"""TST-0005 – Planungsdauer (CON-0005)."""

import time

import pytest

from konfiplaner.planer import PlanerOptionen
from konfiplaner.solver import CpSatPlaner
from tests.helfer import mit_regeln, zufallsmodell

pytestmark = pytest.mark.performance


def test_500_personen_30_themen_40_slots_unter_60_sekunden():
    m = zufallsmodell(500, 30, 40)
    t0 = time.perf_counter()
    plan = CpSatPlaner().planen(m, mit_regeln(), PlanerOptionen(zeitlimit_s=60))
    dauer = time.perf_counter() - t0
    assert plan.status in ("optimal", "machbar"), plan.begruendung
    assert dauer <= 62  # Limit gilt für den gesamten Aufruf; 2 s Toleranz für Auslesen des Plans
