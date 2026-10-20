"""Hinweis auf neuere Versionen im öffentlichen Release (SPEC-0015)."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from importlib import metadata
from typing import Any, Protocol

REPOSITORY = "borisbrue/konfiplaner"
RELEASE_API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
ZEITLIMIT_S = 5


def eigene_version() -> str:
    """Version aus den Paketdaten (`pyproject.toml`); ohne Installation „0.0.0“."""
    try:
        return metadata.version("konfiplaner")
    except metadata.PackageNotFoundError:
        return "0.0.0"


def parse_version(text: str) -> tuple[int, ...] | None:
    """„v0.10.0“ → (0, 10, 0); alles Unlesbare → None."""
    treffer = re.fullmatch(r"v?(\d+(?:\.\d+){0,3})", str(text).strip())
    return tuple(int(t) for t in treffer.group(1).split(".")) if treffer else None


def _auffuellen(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    n = max(len(a), len(b))
    return a + (0,) * (n - len(a)), b + (0,) * (n - len(b))


def ist_neuer(eigene: str, release: str) -> bool:
    """True, wenn `release` numerisch höher ist als `eigene`."""
    e, r = parse_version(eigene), parse_version(release)
    if e is None or r is None:
        return False
    e, r = _auffuellen(e, r)
    return r > e


class UpdateFehler(Exception):
    """Die Abfrage ist fehlgeschlagen (keine Verbindung, Zeitüberschreitung, ungültige Antwort)."""


@dataclass(frozen=True)
class UpdateInfo:
    version: str  # ohne führendes „v“
    url: str  # Release-Seite


class UpdateQuelle(Protocol):
    def neueste(self) -> dict[str, Any] | None:
        """Antwort der Releases-Schnittstelle als Wörterbuch; None, wenn es kein Release gibt."""
        ...


class GitHubQuelle:
    """Fragt das neueste stabile Release anonym ab; sendet nur Programmname und Version."""

    def __init__(self, version: str | None = None, url: str = RELEASE_API) -> None:
        self.url = url
        self.agent = f"KonfiPlaner/{version or eigene_version()}"

    def neueste(self) -> dict[str, Any] | None:
        anfrage = urllib.request.Request(
            self.url, headers={"User-Agent": self.agent, "Accept": "application/vnd.github+json"}
        )
        try:
            with urllib.request.urlopen(anfrage, timeout=ZEITLIMIT_S) as antwort:
                daten = json.load(antwort)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise UpdateFehler(f"HTTP {e.code}") from e
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            raise UpdateFehler(str(e)) from e
        if not isinstance(daten, dict):
            raise UpdateFehler("Unerwartete Antwort")
        return daten


def suche_update(quelle: UpdateQuelle, eigene: str) -> UpdateInfo | None:
    """Die neuere Version, falls es eine gibt; `UpdateFehler` bei Problemen mit der Quelle."""
    try:
        daten = quelle.neueste()
    except UpdateFehler:
        raise
    except (OSError, ValueError) as e:
        raise UpdateFehler(str(e)) from e
    if not daten or daten.get("draft") or daten.get("prerelease"):
        return None
    tag, url = daten.get("tag_name"), daten.get("html_url")
    if not isinstance(tag, str) or not isinstance(url, str) or not ist_neuer(eigene, tag):
        return None
    return UpdateInfo(tag.removeprefix("v"), url)
