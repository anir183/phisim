from pathlib import Path

_SOURCE_ROOT = Path(__file__).resolve().parents[3]
_PACKAGE_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = (
    _SOURCE_ROOT
    if (_SOURCE_ROOT / "web").is_dir() and (_SOURCE_ROOT / "src").is_dir()
    else _PACKAGE_ROOT
)

DATA_DIR = PROJECT_ROOT / "data"
DB_FILE = DATA_DIR / "phisim.db"
WEB_DIR = PROJECT_ROOT / "web"
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"
