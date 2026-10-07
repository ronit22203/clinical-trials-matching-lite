"""Service entrypoint for parse, index, query, and graph inspection."""

from __future__ import annotations

import argparse
import subprocess
import sys

from healthcare_platform_lite.query_engine import PROJECT_ROOT, run_index, run_query

SCRIPTS = PROJECT_ROOT / "scripts"


def _run_script(script_name: str, script_args: list[str]) -> int:
    script = SCRIPTS / script_name
    completed = subprocess.run([sys.executable, str(script), *script_args], cwd=PROJECT_ROOT)
    return completed.returncode


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Healthcare platform lite")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_parser = subparsers.add_parser("parse", help="OCR raw PDFs into data/input")
    parse_parser.add_argument("--input", default="data/raw_documents")
    parse_parser.add_argument("--output", default="data/input")

    subparsers.add_parser("index", help="Build the GraphRAG index from config/settings.yaml")

    query_parser = subparsers.add_parser("query", help="Query the indexed graph")
    query_parser.add_argument("question")
    query_parser.add_argument(
        "--method",
        choices=("local", "global", "drift", "basic"),
        default="local",
    )

    visualize_parser = subparsers.add_parser(
        "visualize",
        help="Print entities and relationships from data/output",
    )
    visualize_parser.add_argument("--output", default="data/output")
    visualize_parser.add_argument("--limit", type=int, default=20)

    args = parser.parse_args(argv)
    if args.command == "parse":
        raise SystemExit(
            _run_script("parse_pdfs.py", ["--input", args.input, "--output", args.output])
        )
    if args.command == "index":
        run_index()
        return
    if args.command == "query":
        print(run_query(args.question, args.method), end="")
        return
    if args.command == "visualize":
        raise SystemExit(
            _run_script(
                "visualize_graph.py",
                ["--output", args.output, "--limit", str(args.limit)],
            )
        )


if __name__ == "__main__":
    main()
