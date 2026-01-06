from __future__ import annotations

import argparse

from .runner import run_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(prog="obrbr", description="Offline RAG Benchmark Runner")
    parser.add_argument(
        "--config",
        "-c",
        required=True,
        help="Path to bench.yaml (e.g. configs\\bench.yaml)",
    )
    args = parser.parse_args()
    run_benchmark(config_path=args.config)


if __name__ == "__main__":
    main()
