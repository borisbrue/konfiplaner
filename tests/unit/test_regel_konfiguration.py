"""TST-0007 – Regel-Konfiguration (CON-0007) und Registry."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from konfiplaner.restriktionen import (
    GRUNDREGELN,
    STANDARD_REGISTRY,
    Konfiguration,
    KonfigurationsFehler,
    standard_konfiguration,
)

SCHEMA = json.loads(Path(".sdd/contracts/data/regel-konfiguration.schema.json").read_text())
V = Draft202012Validator(SCHEMA)


@pytest.mark.parametrize(
    "daten",
    [
        {"restriktionen": {"schwerpunkte": {"typ": "weich", "gewicht": 5}}},
        {"restriktionen": {"x": {"typ": "hart", "parameter": {"a": 1}}}},
    ],
)
def test_schema_akzeptiert_gueltige_konfiguration(daten):
    assert not list(V.iter_errors(daten))


@pytest.mark.parametrize(
    "daten",
    [
        {},
        {"restriktionen": {}},
        {"restriktionen": {"x": {}}},
        {"restriktionen": {"x": {"typ": "vielleicht"}}},
        {"restriktionen": {"x": {"typ": "weich", "gewicht": 0}}},
        {"restriktionen": {"x": {"typ": "weich", "gewicht": -1}}},
        {"restriktionen": {"x": {"typ": "hart", "parameter": "text"}}},
        {"restriktionen": {"x": {"typ": "hart", "unbekannt": 1}}},
    ],
)
def test_schema_lehnt_ungueltige_konfiguration_ab(daten):
    assert list(V.iter_errors(daten))


def test_standardkonfiguration_enthaelt_alle_grundregeln_mit_standardtypen():
    k = standard_konfiguration()
    assert set(k.einstellungen) == set(GRUNDREGELN)
    assert k.einstellungen["wichtigkeit"].typ == "weich"
    # Verteilungsregeln (SPEC-0012) sind ohne Profil aus, alle übrigen Grundregeln hart
    for name in ("verteilung", "rangfolge", "ausgleich"):
        assert k.einstellungen[name].typ == "aus"
    assert all(
        e.typ == "hart"
        for n, e in k.einstellungen.items()
        if n not in ("wichtigkeit", "verteilung", "rangfolge", "ausgleich")
    )


def test_konfiguration_ueberschreibt_basis():
    k = Konfiguration.aus_dict(
        {"restriktionen": {"schwerpunkte": {"typ": "weich", "gewicht": 3}}},
        STANDARD_REGISTRY,
        standard_konfiguration(),
    )
    assert k.einstellungen["schwerpunkte"].gewicht == 3.0
    assert k.einstellungen["mindestanzahl"].typ == "hart"


def test_aktive_ohne_ausgeschaltete():
    k = Konfiguration.aus_dict(
        {"restriktionen": {"verfuegbarkeit": {"typ": "aus"}}}, STANDARD_REGISTRY, standard_konfiguration()
    )
    assert "verfuegbarkeit" not in [e.name for e in k.aktive()]


def test_yaml_laden(tmp_path):
    datei = tmp_path / "regeln.yaml"
    datei.write_text("restriktionen:\n  schwerpunkte:\n    typ: weich\n    gewicht: 2\n", encoding="utf-8")
    k = Konfiguration.aus_yaml(datei, STANDARD_REGISTRY, standard_konfiguration())
    assert k.einstellungen["schwerpunkte"].typ == "weich"


def test_ungueltige_konfiguration_nennt_stelle():
    with pytest.raises(KonfigurationsFehler, match="typ"):
        Konfiguration.aus_dict({"restriktionen": {"schwerpunkte": {"typ": "vielleicht"}}}, STANDARD_REGISTRY)
