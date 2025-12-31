import sys
from pathlib import Path

# Ensure project's src/ is on sys.path so tests can import the package without installing
ROOT = Path(__file__).parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
