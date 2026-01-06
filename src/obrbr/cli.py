import typer

from .runner import run_benchmark

app = typer.Typer(add_completion=False, help="Offline RAG Benchmark Runner")


@app.callback(invoke_without_command=True)
def main(
    config: str = typer.Option(..., "--config", "-c", help="Path to bench.yaml"),
) -> None:
    """
    Run benchmark (single-command style).
    Usage:
      python -m obrbr --config configs\\bench.yaml
    """
    run_benchmark(config_path=config)
