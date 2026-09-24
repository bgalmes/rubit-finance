"""Start Rubit Finance locally: ``uv run rubit``."""

import argparse
import threading
import webbrowser

import uvicorn

from rubit.api.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(prog="rubit", description="Run Rubit Finance locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true", help="don't open a browser tab")
    args = parser.parse_args()

    if not args.no_browser:
        url = f"http://{args.host}:{args.port}/"
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    uvicorn.run(create_app(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
