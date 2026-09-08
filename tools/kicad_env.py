#!/usr/bin/env python3
# SPDX-License-Identifier: (GPL-2.0-or-later OR MIT)
"""
G4MEOVER ONE-X — Auffinden von kicad-cli.

Eigene Datei, weil mehrere Werkzeuge sie brauchen (gen_kicad_sch, check_all)
und der Installationsort sich je nach Plattform und Installationsart
unterscheidet: winget legt KiCad unter Windows als Benutzerinstallation nach
%LOCALAPPDATA%\\Programs, eine Systeminstallation nach "Program Files", Linux
und macOS wieder woanders.

Fehlt kicad-cli, ist das kein Fehler, sondern ein SKIP: die KiCad-Pruefungen
entfallen dann sichtbar, statt still zu bestehen (vgl. tools/check_all.py).
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

_CANDIDATES = [
    # Windows, winget-Benutzerinstallation (haeufigster Fall hier)
    Path.home() / "AppData/Local/Programs/KiCad",
    Path("C:/Program Files/KiCad"),
    Path("C:/Program Files (x86)/KiCad"),
    # macOS
    Path("/Applications/KiCad/KiCad.app/Contents/MacOS"),
    # Linux
    Path("/usr/bin"),
    Path("/usr/local/bin"),
]

_EXE = "kicad-cli.exe" if os.name == "nt" else "kicad-cli"


def find_kicad_cli() -> str | None:
    """Pfad zu kicad-cli oder None. $KICAD_CLI hat Vorrang."""
    env = os.environ.get("KICAD_CLI")
    if env and Path(env).is_file():
        return env

    found = shutil.which("kicad-cli")
    if found:
        return found

    for base in _CANDIDATES:
        if not base.exists():
            continue
        if (base / _EXE).is_file():
            return str(base / _EXE)
        # Versionsunterordner (z.B. .../KiCad/10.0/bin/kicad-cli.exe).
        # Neueste Version zuerst, damit nicht zufaellig eine alte gewinnt.
        for sub in sorted(base.glob("*/bin/" + _EXE), reverse=True):
            if sub.is_file():
                return str(sub)
    return None


if __name__ == "__main__":
    cli = find_kicad_cli()
    print(cli if cli else "kicad-cli nicht gefunden")
