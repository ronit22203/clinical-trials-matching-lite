"""Print entities and relationships stored in the GraphRAG parquet output."""

from __future__ import annotations

import argparse
from pathlib import Path


def _read_table(path: Path):
    try:
        import pyarrow.parquet as pq
    except ImportError:
        import pandas as pd

        return pd.read_parquet(path)
    return pq.read_table(path).to_pandas()


def _print_frame(title: str, frame, columns: list[str], limit: int) -> None:
    present = [column for column in columns if column in frame.columns]
    view = frame[present].head(limit) if present else frame.head(limit)
    print(f"\n{title}: {len(frame)} rows")
    if view.empty:
        print("  (empty)")
        return
    for _, row in view.iterrows():
        parts = [f"{column}={row[column]}" for column in view.columns]
        print("  " + " | ".join(parts))
    hidden = len(frame) - len(view)
    if hidden > 0:
        print(f"  ... {hidden} more")


def visualize(output_dir: Path, limit: int) -> None:
    """Summarize graph tables if indexing has written them."""
    if not output_dir.is_dir():
        raise SystemExit(f"Output directory does not exist: {output_dir}")

    entities = output_dir / "entities.parquet"
    relationships = output_dir / "relationships.parquet"
    if not entities.exists() or not relationships.exists():
        present = sorted(path.name for path in output_dir.glob("*.parquet"))
        raise SystemExit(
            "Graph tables are not in the output yet "
            f"(have: {', '.join(present) or 'none'}). "
            "Finish `make index` to produce entities.parquet and relationships.parquet."
        )

    try:
        entity_frame = _read_table(entities)
        relationship_frame = _read_table(relationships)
    except ImportError as error:
        raise SystemExit(
            "Reading parquet requires pyarrow or pandas. Install one with "
            "`uv pip install pyarrow`."
        ) from error

    _print_frame(
        "Entities",
        entity_frame,
        ["title", "type", "description"],
        limit,
    )
    _print_frame(
        "Relationships",
        relationship_frame,
        ["source", "target", "description", "weight"],
        limit,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/output"),
        help="GraphRAG output directory",
    )
    parser.add_argument("--limit", type=int, default=20, help="Rows to print per table")
    args = parser.parse_args(argv)
    visualize(args.output, args.limit)


if __name__ == "__main__":
    main()
