"""Benchmark candidate scalar APIs against stdlib and pinned published fastuuid7."""

if __package__:
    from .benchmark_competitors import main
else:
    from benchmark_competitors import main

if __name__ == "__main__":
    raise SystemExit(main(scalar_only=True))
