"""Agent Glyphs: the icon index and the code that searches, measures and exports it."""

import sys

# checked here, before any module that needs newer Python is loaded, so the person
# sees what to do instead of a SyntaxError from deep inside the package
if sys.version_info < (3, 9):
    raise SystemExit(
        f"Agent Glyphs needs Python 3.9 or newer (this is {sys.version.split()[0]}). "
        "Install a newer Python, or run the script with uv: uv run --python 3.12 scripts/search.py ..."
    )
