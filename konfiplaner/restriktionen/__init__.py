from konfiplaner.restriktionen.basis import (
    Konfiguration,
    KonfigurationsFehler,
    RegelEinstellung,
    RegistrierungsFehler,
    Registry,
    Restriktion,
)
from konfiplaner.restriktionen.grundregeln import GRUNDREGELN, STANDARD_REGISTRY, restriktion
from konfiplaner.restriktionen.kontext import Planungskontext

__all__ = [
    "GRUNDREGELN",
    "STANDARD_REGISTRY",
    "Konfiguration",
    "KonfigurationsFehler",
    "Planungskontext",
    "RegelEinstellung",
    "RegistrierungsFehler",
    "Registry",
    "Restriktion",
    "restriktion",
]


def standard_konfiguration() -> Konfiguration:
    return Konfiguration.standard(STANDARD_REGISTRY, GRUNDREGELN)
