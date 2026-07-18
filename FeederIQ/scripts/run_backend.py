"""Launch the FeederIQ FastAPI backend."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Ensure the project root is on the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn


def _ensure_public_codespaces_port(port: int) -> None:
    """Best-effort: make the app port public when running in GitHub Codespaces."""
    codespace_name = os.getenv("CODESPACE_NAME")
    if not codespace_name:
        return

    gh_path = shutil.which("gh")
    if not gh_path:
        print(f"[run_backend] 'gh' CLI not found. Skipping public port setup for {port}.")
        return

    result = subprocess.run(
        [
            gh_path,
            "codespace",
            "ports",
            "visibility",
            f"{port}:public",
            "-c",
            codespace_name,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip() or "unknown error"
        print(
            f"[run_backend] Unable to mark port {port} public. "
            f"Run manually: gh codespace ports visibility {port}:public -c \"$CODESPACE_NAME\". "
            f"Details: {details}"
        )

if __name__ == "__main__":
    _ensure_public_codespaces_port(8000)
    uvicorn.run("feederiq.backend.main:app", host="0.0.0.0", port=8000, reload=True)
