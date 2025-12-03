import sys
from pathlib import Path

# Insert project root so `scripts` package can be imported
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from scripts.frontend.ui import run_app

if __name__ == "__main__":
    run_app()