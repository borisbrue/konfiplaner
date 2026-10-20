"""TST-0031 – Version, Vergleich, Antwort lesen, Takt und Einstellungen (CON-0020)."""

import http.server
import json
import threading
import tomllib
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from konfiplaner.anwendung import Sitzung
from konfiplaner.einstellungen import YamlEinstellungen
from konfiplaner.update import (
    GitHubQuelle,
    UpdateFehler,
    UpdateInfo,
    eigene_version,
    ist_neuer,
    parse_version,
    suche_update,
)

RELEASE = {"tag_name": "v0.2.0", "html_url": "https://example.invalid/r/v0.2.0"}


class Fest:
    def __init__(self, antwort=None, fehler=None):
        self.antwort, self.fehler = antwort, fehler

    def neueste(self):
        if self.fehler:
            raise self.fehler
        return self.antwort


@pytest.mark.parametrize(
    ("eigene", "release", "neuer"),
    [
        ("0.1.0", "v0.2.0", True),
        ("0.9.0", "0.10.0", True),
        ("0.2.0", "v0.2.0", False),
        ("0.2.0", "v0.1.9", False),
        ("0.1.0", "latest", False),
        ("0.1", "0.1.0", False),
        ("0.1.0", "v1", True),
        ("kaputt", "v9.9.9", False),
    ],
)
def test_versionsvergleich(eigene, release, neuer):
    assert ist_neuer(eigene, release) is neuer


def test_version_lesen():
    assert parse_version("v0.10.0") == (0, 10, 0) and parse_version("x1") is None


def test_version_stammt_aus_pyproject():
    pyproject = Path(__file__).parents[2] / "pyproject.toml"
    assert eigene_version() == tomllib.loads(pyproject.read_text())["project"]["version"]


def test_suche_update_meldet_nur_hoehere_stabile_versionen():
    assert suche_update(Fest(RELEASE), "0.1.0") == UpdateInfo("0.2.0", RELEASE["html_url"])
    assert suche_update(Fest(RELEASE), "0.2.0") is None
    assert suche_update(Fest({**RELEASE, "prerelease": True}), "0.1.0") is None
    assert suche_update(Fest({**RELEASE, "draft": True}), "0.1.0") is None
    assert suche_update(Fest({**RELEASE, "tag_name": "nightly"}), "0.1.0") is None
    assert suche_update(Fest({"tag_name": "v0.2.0"}), "0.1.0") is None  # ohne Adresse
    assert suche_update(Fest(None), "0.1.0") is None  # kein Release


def test_suche_update_wandelt_fehler_der_quelle():
    with pytest.raises(UpdateFehler):
        suche_update(Fest(fehler=UpdateFehler("weg")), "0.1.0")
    with pytest.raises(UpdateFehler):
        suche_update(Fest(fehler=OSError("netz")), "0.1.0")


class Server:
    """Ein lokaler HTTP-Server, der die Anfrage protokolliert (kein Netz nötig)."""

    def __init__(self, status=200, koerper=b"{}"):
        server = self
        self.anfragen = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                server.anfragen.append((self.path, dict(self.headers)))
                self.send_response(status)
                self.end_headers()
                self.wfile.write(koerper)

            def log_message(self, *args):
                pass

        self.httpd = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}/releases/latest"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def schliessen(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def test_abfrage_sendet_nur_adresse_und_user_agent():
    s = Server(200, json.dumps(RELEASE).encode())
    try:
        assert GitHubQuelle("1.2.3", s.url).neueste() == RELEASE
    finally:
        s.schliessen()
    pfad, kopf = s.anfragen[0]
    assert pfad == "/releases/latest" and kopf["User-Agent"] == "KonfiPlaner/1.2.3"
    erlaubt = {"Host", "User-Agent", "Accept", "Accept-Encoding", "Connection"}
    assert set(kopf) <= erlaubt  # keine Cookies, keine eigenen Daten


@pytest.mark.parametrize(
    ("status", "koerper", "erwartet"),
    [
        (404, b"", None),
        (500, b"", UpdateFehler),
        (200, b"kein json", UpdateFehler),
        (200, b"[1]", UpdateFehler),
    ],
)
def test_antworten_und_fehler_der_schnittstelle(status, koerper, erwartet):
    s = Server(status, koerper)
    try:
        quelle = GitHubQuelle("0.1.0", s.url)
        if erwartet is None:
            assert quelle.neueste() is None
        else:
            with pytest.raises(erwartet):
                quelle.neueste()
    finally:
        s.schliessen()


def test_ohne_verbindung_ist_ein_update_fehler():
    with pytest.raises(UpdateFehler):
        GitHubQuelle("0.1.0", "http://127.0.0.1:9/x").neueste()


def test_takt_abschalten_und_ausblenden_bleiben_erhalten(tmp_path):
    pfad = tmp_path / "e.yaml"
    s = Sitzung(YamlEinstellungen(pfad))
    jetzt = datetime(2026, 11, 1, 12, 0)
    assert s.update_faellig(jetzt)  # noch nie geprüft
    s.markiere_update_geprueft(jetzt)
    assert not s.update_faellig(jetzt + timedelta(hours=23, minutes=59))
    assert s.update_faellig(jetzt + timedelta(hours=24))
    s.blende_update_aus("0.2.0")
    neu = Sitzung(YamlEinstellungen(pfad))
    assert neu.ausgeblendete_version == "0.2.0" and neu.letzte_updatepruefung == jetzt
    neu.update_pruefung = False
    assert not neu.update_faellig(jetzt + timedelta(days=30))
    neu.speichere()
    assert Sitzung(YamlEinstellungen(pfad)).update_pruefung is False
