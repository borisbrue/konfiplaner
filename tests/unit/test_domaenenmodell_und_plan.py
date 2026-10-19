"""TST-0003 – Domänenmodell und Plan (CON-0003)."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from konfiplaner.modell import Modell, ModellFehler, Person, Plan, Termin, Thema, Verstoss
from tests.helfer import modell, slots

SCHEMA = json.loads(Path(".sdd/contracts/data/domaenenmodell-und-plan.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)


def test_person_braucht_genau_zwei_verschiedene_themen():
    with pytest.raises(ModellFehler):
        Person("A", ("X", "X"))
    with pytest.raises(ModellFehler):
        Person(name="A", themen=("X",))


@pytest.mark.parametrize(
    "feld,wert", [("wichtigkeit", 0), ("wichtigkeit", 6), ("mindestanzahl", 0), ("dauer_min", 0)]
)
def test_thema_wertebereiche(feld, wert):
    with pytest.raises(ModellFehler):
        Thema("T", **{feld: wert})


def test_modell_lehnt_unbekannte_themen_und_doppelte_namen_ab():
    with pytest.raises(ModellFehler):
        modell([Thema("A")], [("P", "A", "B")])
    with pytest.raises(ModellFehler):
        modell([Thema("A"), Thema("A")], [])


@pytest.mark.parametrize("dauer,erwartet", [(45, 1), (90, 2), (100, 3)])
def test_dauer_wird_auf_ganze_slots_aufgerundet(dauer, erwartet):
    m = modell([Thema("A", dauer_min=dauer)], [], n_slots=5)
    assert m.bloecke("A")[0] == erwartet


def test_bloecke_beachten_tagesgrenzen():
    m = Modell([Thema("A", dauer_min=90)], [], slots(1, "Mo") + slots(1, "Di"))
    assert m.bloecke("A") == {}


def test_plan_entspricht_schema():
    plan = Plan("machbar", [Termin("A", 0, 2, ("x", "y"))], [Verstoss("wichtigkeit", "text")], seed=1)
    assert not list(VALIDATOR.iter_errors(plan.to_dict()))


def test_kein_plan_braucht_begruendung_und_hat_keine_termine():
    assert list(VALIDATOR.iter_errors({"status": "kein_plan", "termine": []}))
    assert not list(VALIDATOR.iter_errors(Plan("kein_plan", begruendung=["x"]).to_dict()))
    assert list(
        VALIDATOR.iter_errors(
            {
                "status": "kein_plan",
                "begruendung": ["x"],
                "termine": [{"thema": "A", "start_slot": 0, "anzahl_slots": 1, "teilnehmer": []}],
            }
        )
    )
