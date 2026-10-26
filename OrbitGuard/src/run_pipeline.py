"""Single entrypoint: ingest -> propagate (SGP4) -> KD-tree screening -> DuckDB.

Usage (from the project root):
    python -m src.run_pipeline --hours 24 --step 10
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config.settings import FORECAST_HOURS, STEP_MINUTES, SAFETY_DISTANCE_KM  # noqa: E402
from src.ingestion.celestrak_ingest import run_ingestion  # noqa: E402
from src.engine.sgp4_propagator import load_satellites, make_times, propagate  # noqa: E402
from src.engine.collision_risk import CollisionRiskEngine  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="OrbitGuard end-to-end pipeline")
    ap.add_argument("--hours", type=int, default=FORECAST_HOURS, help="forecast window (default 72)")
    ap.add_argument("--step", type=int, default=STEP_MINUTES, help="minutes per timestep (default 10)")
    ap.add_argument("--force", action="store_true", help="re-download data even if cache is fresh")
    ap.add_argument("--threshold-km", type=float, default=SAFETY_DISTANCE_KM,
                    help="conjunction distance threshold in km")
    ap.add_argument("--max-sats", type=int, default=0, help="limit number of satellites (0 = all)")
    ap.add_argument("--file", default=None, help="use this GP JSON instead of downloading")
    args = ap.parse_args(argv)

    start = time.time()
    path = args.file or run_ingestion(force=args.force)          # 1. ingestion
    if not path:
        print("Pipeline aborted: no orbital data available.")
        return 1

    sats, meta = load_satellites(path)                           # 2. load
    if args.max_sats:
        sats, meta = sats[:args.max_sats], meta[:args.max_sats]
    if not sats:
        print("Pipeline aborted: no valid satellites in the data file.")
        return 1

    times = make_times(hours=args.hours, step_minutes=args.step)  # 3. propagate
    states = propagate(sats, meta, times)

    with CollisionRiskEngine(threshold_km=args.threshold_km) as engine:  # 4. screen + store
        total = sum(engine.evaluate_conjunctions(df, t) for t, df in states.items())
        levels = engine.counts_by_level()                        # connection closes on exit

    print("\n=== OrbitGuard summary ===")                         # 5. summary
    print(f"Objects loaded : {len(sats)}")
    print(f"Timesteps      : {len(times)} ({args.hours} h, every {args.step} min)")
    print(f"Threshold      : {args.threshold_km} km")
    print(f"Alerts stored  : {total}")
    for level in ("CRITICAL", "WARNING"):
        print(f"  {level:<9}: {levels.get(level, 0)}")
    print(f"Elapsed        : {time.time() - start:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())