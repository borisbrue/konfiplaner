import os

# Alle Tests, die Qt berühren, laufen ohne Bildschirm
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
