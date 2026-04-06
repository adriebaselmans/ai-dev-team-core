from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent
AI_TEAM_ROOT = REPO_ROOT / ".ai-team"
if str(AI_TEAM_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_TEAM_ROOT))

from team_orchestrator.cli import main as cli_main


def main() -> int:
    return cli_main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
