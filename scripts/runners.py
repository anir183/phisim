import subprocess
import sys
from pathlib import Path

import uvicorn

from phisim.main import app
from phisim.utils.env import settings


def phisim() -> None:
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
    )


def dev() -> None:
    uvicorn.run(
        "phisim.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


def test() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest"],
    )

    if result.returncode not in (0, 5):
        raise SystemExit(result.returncode)


def lint() -> None:
    subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."],
        check=True,
    )


def format() -> None:
    subprocess.run(
        [sys.executable, "-m", "ruff", "format", "."],
        check=True,
    )


def typecheck() -> None:
    subprocess.run(
        [sys.executable, "-m", "pyright"],
        check=True,
    )


def check() -> None:
    lint()
    subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--check", "."],
        check=True,
    )
    typecheck()
    test()


def clean() -> None:
    root = Path(__file__).resolve().parent.parent

    for path in root.rglob("__pycache__"):
        if path.is_dir():
            print(f"Removing {path}")
            import shutil

            shutil.rmtree(path)

    for pattern in ("*.pyc", "*.pyo"):
        for path in root.rglob(pattern):
            if path.is_file():
                print(f"Removing {path}")
                path.unlink()
