import argparse
import json
from pathlib import Path

from app.config import Settings
from app.main import create_app


def main() -> None:
    """Write the backend-owned API schema for generated clients and drift checks."""
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    settings = Settings(
        _env_file=None,
        basic_auth_username="schema",
        basic_auth_password="schema-only",
    )
    schema = create_app(settings=settings).openapi()
    args.output.write_text(
        f"{json.dumps(schema, indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
