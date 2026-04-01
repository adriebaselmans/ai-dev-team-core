from __future__ import annotations

import sys

from team_orchestrator.cli import main as cli_main


def main() -> int:
    return cli_main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
