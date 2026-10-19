"""TST-0001 – Importergebnis und Fehlerliste (CON-0001)."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from konfiplaner.excel_import import importiere
from tests.xlsx_helfer import PERSONEN, SLOTS, THEMEN, schreibe

SCHEMA = json.loads(Path(".sdd/contracts/data/importmodell-und-fehlerliste.schema.json").read_text())
V = Draft202012Validator(SCHEMA)


def test_erfolgreicher_import_entspricht_dem_schema(tmp_path):
    erg = importiere(
        schreibe(tmp_path / "a.xlsx", {"Personen": PERSONEN, "Themen": THEMEN, "Zeitslots": SLOTS})
    )
    d = erg.to_dict()
    assert "modell" in d and not list(V.iter_errors(d))


def test_fehlerhafter_import_hat_kein_modell_und_entspricht_dem_schema(tmp_path):
    kaputt = [["Name", "Thema 1", "Thema 2"], ["Anna", "X", "X"]]
    erg = importiere(
        schreibe(tmp_path / "a.xlsx", {"Personen": kaputt, "Themen": THEMEN, "Zeitslots": SLOTS})
    )
    d = erg.to_dict()
    assert "modell" not in d and d["meldungen"] and not list(V.iter_errors(d))


def test_schema_verbietet_modell_trotz_fehler():
    d = {
        "meldungen": [{"schwere": "fehler", "blatt": "Personen", "zeile": 2, "spalte": "Name", "text": "x"}],
        "modell": {"personen": [], "themen": []},
    }
    assert list(V.iter_errors(d))
