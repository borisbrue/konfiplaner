import os

# Alle Tests, die Qt berühren, laufen ohne Bildschirm
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import sys

import pytest

_status = {"code": None}


def pytest_sessionfinish(session, exitstatus):
    _status["code"] = int(exitstatus)


@pytest.hookimpl(trylast=True)
def pytest_unconfigure(config):
    """Beendet nach dem Testlauf hart: Qt räumt beim normalen Interpreter-Ende gelegentlich
    Objekte doppelt ab (Abbruch mit Code 134 trotz grüner Tests)."""
    if _status["code"] is not None:
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(_status["code"])
