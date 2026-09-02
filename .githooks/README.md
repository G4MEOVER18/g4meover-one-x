# .githooks — repo-verfolgte Git-Hooks

## Aktivieren
```
python tools/install_hooks.py
```
Setzt `core.hooksPath` auf dieses Verzeichnis (idempotent). Danach läuft vor jedem Commit:

## `pre-commit`
Führt `python tools/check_all.py` aus — das aggregierte grüne Tor (read-only):
1. `spec_validator.py --check` — keine verbotenen Claims / Spec-Konsistenz
2. `schematic_netcheck.py` — Inter-Board-Netznamen beidseitig gespiegelt
3. `gen_kicad_project.py --check` — KiCad-Ableitung reproduzierbar + selbstgeprüft

**Read-only:** Alle drei laufen im `--check`-Modus und schreiben **nichts** — der Hook verändert den Arbeitsbaum nicht. Bei FAIL wird der Commit abgebrochen.

Bewusst umgehen (nur mit Grund): `git commit --no-verify`.

> Hinweis: Hooks sind lokal pro Clone. Jeder, der am Repo arbeitet (auch die 6h-Cloud-Routine), aktiviert sie einmalig via `install_hooks.py`. Ohne Aktivierung bleibt das Verhalten unverändert.

## Serverseitiger Spiegel (CI)
Unabhängig vom lokalen Hook läuft `check_all.py` auch in **GitHub Actions** ([`.github/workflows/verify.yml`](../.github/workflows/verify.yml)) bei jedem Push/PR auf `main` — plus ein **Determinismus-Check**, der `spec_validator.py` + `gen_kicad_project.py` neu laufen lässt und bei einem Diff fehlschlägt (fängt veraltete abgeleitete Dateien). So greift das grüne Tor auch, wenn jemand den lokalen Hook nicht aktiviert hat.
