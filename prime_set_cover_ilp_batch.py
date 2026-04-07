#!/usr/bin/env python3
"""
Run ILP set cover for each n in a range: time each run, print a one-line summary,
and append the same (plus timestamp) to a log file. Continues on skip/errors.
"""

from __future__ import annotations

import argparse
import time
import traceback
from datetime import datetime, timezone

from prime_set_cover import build_set_cover_instance
from set_cover import ilp_set_cover


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch ILP for prime-point line set cover: one n at a time, "
        "log + print timing and objective."
    )
    parser.add_argument(
        "--from",
        dest="n_start",
        type=int,
        default=2,
        metavar="N0",
        help="first n (default: 2)",
    )
    parser.add_argument(
        "--to",
        dest="n_end",
        type=int,
        default=None,
        metavar="N1",
        help="last n (inclusive); omit with --forever to run n, n+1, … until Ctrl+C",
    )
    parser.add_argument(
        "--forever",
        action="store_true",
        help="ignore --to: start at --from and increase n forever (stop with Ctrl+C)",
    )
    parser.add_argument(
        "--log",
        type=str,
        default="prime_set_cover_ilp.log",
        metavar="FILE",
        help="append results here (default: prime_set_cover_ilp.log)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="also print full line descriptions for each optimal cover (noisy for large n)",
    )
    args = parser.parse_args()

    if args.forever:
        if args.n_end is not None:
            raise SystemExit("use either --forever or --to, not both")
    else:
        if args.n_end is None:
            raise SystemExit("need --to N1 or use --forever")
        if args.n_end < args.n_start:
            raise SystemExit("--to must be >= --from")
        n_iter = range(args.n_start, args.n_end + 1)
    if args.n_start < 2:
        raise SystemExit("--from must be at least 2")

    from prime_lines import format_line_human

    log_path = args.log
    with open(log_path, "a", encoding="utf-8") as logf:

        def emit(msg: str) -> None:
            print(msg, flush=True)
            logf.write(msg + "\n")
            logf.flush()

        if args.forever:
            emit(
                f"# batch start {utc_now_iso()} forever from n={args.n_start} "
                f"(Ctrl+C to stop)"
            )
        else:
            emit(
                f"# batch start {utc_now_iso()} range n=[{args.n_start},{args.n_end}]"
            )

        def run_one(n: int) -> None:
            t_wall0 = time.perf_counter()
            try:
                t_build0 = time.perf_counter()
                points, subsets, triples = build_set_cover_instance(n)
                t_build1 = time.perf_counter()
                build_s = t_build1 - t_build0
                m_lines = len(subsets)
                universe = set(range(n))
                costs = [1.0] * m_lines

                t_ilp0 = time.perf_counter()
                opt = ilp_set_cover(universe, subsets, costs)
                t_ilp1 = time.perf_counter()
                ilp_s = t_ilp1 - t_ilp0
                total_s = time.perf_counter() - t_wall0
                opt_cost = sum(costs[i] for i in opt)

                line = (
                    f"{utc_now_iso()}\tn={n}\tok\tm_lines={m_lines}\t"
                    f"build_s={build_s:.6f}\tilp_s={ilp_s:.6f}\topt={int(opt_cost)}\t"
                    f"indices={opt!s}\ttotal_s={total_s:.6f}"
                )
                emit(line)

                if args.verbose:
                    for i in opt:
                        print(" ", format_line_human(triples[i], points), flush=True)
                    logf.flush()

            except Exception:
                total_s = time.perf_counter() - t_wall0
                err = traceback.format_exc().replace("\n", " | ")
                line = (
                    f"{utc_now_iso()}\tn={n}\terror\tbuild_s=\tilp_s=\topt=\t"
                    f"total_s={total_s:.6f}\t{err}"
                )
                emit(line)

        try:
            if args.forever:
                n = args.n_start
                while True:
                    run_one(n)
                    n += 1
            else:
                for n in n_iter:
                    run_one(n)
        except KeyboardInterrupt:
            emit(f"# interrupted {utc_now_iso()}")

        emit(f"# batch end {utc_now_iso()}")


if __name__ == "__main__":
    main()
