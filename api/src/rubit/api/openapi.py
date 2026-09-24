"""Write the OpenAPI schema used to generate the frontend types."""

import json
import sys
from pathlib import Path

from rubit.api.app import Settings, create_app


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("openapi.json")
    schema = create_app(Settings(web_dir=None)).openapi()
    target.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {target}")


if __name__ == "__main__":
    main()
