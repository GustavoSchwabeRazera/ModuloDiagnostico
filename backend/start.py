"""Inicializa o backend de forma portável, aplicando migrações antes da API."""

from __future__ import annotations

import os
import subprocess
import sys


def main() -> None:
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    port = os.getenv("PORT", "8000")
    os.execvp(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            port,
            "--proxy-headers",
            "--forwarded-allow-ips",
            os.getenv("FORWARDED_ALLOW_IPS", "*"),
        ],
    )


if __name__ == "__main__":
    main()
