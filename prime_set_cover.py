#!/usr/bin/env python3
"""
Set cover: universe = prime points (k, p_k), sets = collinear subsets (≥2 points
on one line). Uses prime_lines to build the family of lines, then set_cover.
"""

from __future__ import annotations

import argparse

from prime_lines import format_line_human, lines_with_point_indices
from set_cover import exact_set_cover_bitmask, greedy_set_cover, ilp_set_cover


def build_set_cover_instance(
    count: int,
) -> tuple[list[tuple[int, int]], list[set[int]], list[tuple[int, int, int]]]:
    points, line_items = lines_with_point_indices(count)
    triples: list[tuple[int, int, int]] = []
    subsets: list[set[int]] = []
    for line, idxs in line_items:
        if len(idxs) >= 2:
            triples.append(line)
            subsets.append(set(idxs))
    return points, subsets, triples


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Minimum set cover: cover all prime points with fewest lines "
        "(each line covers the primes collinear on it)."
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=30,
        metavar="N",
        help="number of prime points (default: 30)",
    )
    parser.add_argument(
        "--method",
        choices=("greedy", "ilp", "exact", "all"),
        default="ilp",
        help="solver: greedy, ILP (CBC), exact bitmask (tiny only), or all",
    )
    parser.add_argument(
        "--ilp-max-sets",
        type=int,
        default=15_000,
        metavar="M",
        help="skip ILP if number of lines exceeds this (default: 15000)",
    )
    args = parser.parse_args()
    if args.count < 2:
        raise SystemExit("need at least 2 points")

    points, subsets, triples = build_set_cover_instance(args.count)
    n_pts = len(points)
    m_lines = len(subsets)
    universe = set(range(n_pts))

    print(f"Points: {n_pts}, lines with ≥2 collinear points: {m_lines}\n")

    costs = [1.0] * m_lines

    def describe(indices: list[int]) -> None:
        for i in indices:
            print(" ", format_line_human(triples[i], points))

    def run_greedy() -> None:
        g = greedy_set_cover(universe, subsets, costs)
        print(
            "greedy:",
            len(g),
            "lines, cost",
            sum(costs[i] for i in g),
            "set indices",
            g,
        )
        describe(g)

    def run_ilp() -> None:
        if m_lines > args.ilp_max_sets:
            print(
                f"ilp: skipped ({m_lines} sets > --ilp-max-sets {args.ilp_max_sets})"
            )
            return
        opt = ilp_set_cover(universe, subsets, costs)
        print(
            "ILP:  ",
            len(opt),
            "lines, cost",
            sum(costs[i] for i in opt),
            "set indices",
            opt,
        )
        describe(opt)

    def run_exact() -> None:
        if m_lines > 28:
            print(f"exact: skipped ({m_lines} sets; bitmask feasible only for ~≤28)")
            return
        e = exact_set_cover_bitmask(universe, subsets, costs)
        print(
            "exact:",
            len(e) if e else None,
            "lines, cost",
            sum(costs[i] for i in e) if e else None,
            "set indices",
            e,
        )
        if e:
            describe(e)

    if args.method == "greedy":
        run_greedy()
    elif args.method == "ilp":
        run_ilp()
    elif args.method == "exact":
        run_exact()
    else:
        run_greedy()
        run_ilp()
        run_exact()


if __name__ == "__main__":
    main()
