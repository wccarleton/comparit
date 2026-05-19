"""Launch the local comparit development server and open a browser.

This script is meant for quick manual checks while the project evolves. It keeps
the setup steps close to the app: create a local config if needed, initialize
the SQLite schema, summarize the configured demo images, start Uvicorn, and
open the homepage once the server is responding.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from urllib.parse import urlencode

from app.core.config import DEFAULT_CONFIG_PATH, PROJECT_ROOT, get_settings
from app.db.connection import connect
from app.db.schema import initialize_schema
from app.db.tokens import create_tokens
from app.services.image_indexer import discover_images
from app.services.tokens import generate_tokens


def parse_args() -> argparse.Namespace:
    """Parse command-line options for the local launcher."""
    parser = argparse.ArgumentParser(description="Launch the comparit development app.")
    parser.add_argument("--host", default="127.0.0.1", help="Host for the local Uvicorn server.")
    parser.add_argument("--port", default=8000, type=int, help="Port for the local Uvicorn server.")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Start the server without opening a browser tab.",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable Uvicorn reload mode.",
    )
    parser.add_argument(
        "--token",
        help="Open the app with an existing participant token instead of generating one.",
    )
    return parser.parse_args()


def ensure_local_config() -> None:
    """Create `config.toml` from the example file when it is missing."""
    example_path = PROJECT_ROOT / "config.example.toml"
    if DEFAULT_CONFIG_PATH.exists():
        return

    shutil.copyfile(example_path, DEFAULT_CONFIG_PATH)
    print(
        f"Created {DEFAULT_CONFIG_PATH.relative_to(PROJECT_ROOT)} from config.example.toml.",
        flush=True,
    )


def initialize_database() -> None:
    """Initialize the configured SQLite schema."""
    with connect() as connection:
        initialize_schema(connection)
    print("Database initialized.", flush=True)


def summarize_images() -> None:
    """Print how many configured demo images are available."""
    settings = get_settings()
    images = discover_images(settings.resolved_image_root, settings.allowed_extensions)
    image_root = settings.resolved_image_root.relative_to(PROJECT_ROOT)
    print(f"Found {len(images)} image(s) below {image_root}.", flush=True)


def wait_for_health(url: str, timeout_seconds: float = 20.0) -> bool:
    """Wait for the local health endpoint to respond."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                return response.status == 200
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(0.25)
    return False


def launch_server(host: str, port: int, reload: bool) -> subprocess.Popen[bytes]:
    """Start Uvicorn as a child process."""
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        command.append("--reload")

    print(f"Starting server at http://{host}:{port}", flush=True)
    return subprocess.Popen(command, cwd=PROJECT_ROOT)


def browser_url(host: str, port: int, token: str | None) -> str:
    """Build the browser URL, generating a development token when needed."""
    settings = get_settings()
    homepage_url = f"http://{host}:{port}"
    if not settings.token_required:
        return homepage_url

    if token is None:
        token = generate_tokens(1)[0]
        create_tokens([token], validity_days=settings.token_validity_days)
        print("Generated a local development participant token.", flush=True)

    return f"{homepage_url}/?{urlencode({'t': token})}"


def print_participant_url(url: str) -> None:
    """Print the participant URL in a copy-friendly block."""
    border = "=" * 72
    print(border, flush=True)
    print("Participant URL - copy this to reopen the same dev session:", flush=True)
    print(url, flush=True)
    print(border, flush=True)


def main() -> int:
    """Run the development launcher."""
    args = parse_args()

    ensure_local_config()
    initialize_database()
    summarize_images()
    homepage_url = browser_url(args.host, args.port, args.token)
    health_url = f"http://{args.host}:{args.port}/health"
    print_participant_url(homepage_url)

    process = launch_server(args.host, args.port, reload=not args.no_reload)
    try:
        if wait_for_health(health_url):
            print(f"Server is ready: {homepage_url}", flush=True)
            print_participant_url(homepage_url)
            if not args.no_browser:
                webbrowser.open(homepage_url)
                print("Browser launch requested.", flush=True)
        else:
            print(f"Server did not respond at {health_url} before the timeout.", flush=True)

        return process.wait()
    except KeyboardInterrupt:
        print("\nStopping server.", flush=True)
        process.terminate()
        return process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
