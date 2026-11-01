"""Run the launch-engine command-line interface from the project root."""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from agents.supervisor import main


if __name__ == "__main__":
    raise SystemExit(main())
