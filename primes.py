#!/usr/bin/env python3
"""Generate the first n primes as (index, prime) pairs: (1, 2), (2, 3), (3, 5), ..."""

from __future__ import annotations

import argparse


def first_n_primes(count: int) -> list[int]:
    """Return the first `count` primes, smallest first."""
    if count < 1:
        return []
    primes: list[int] = [2]
    candidate = 3
    while len(primes) < count:
        limit = int(candidate**0.5) + 1
        if all(candidate % p != 0 for p in primes if p < limit):
            primes.append(candidate)
        candidate += 2
    return primes


def prime_points(count: int) -> list[tuple[int, int]]:
    """Pairs (k, p_k) for k = 1 .. count, where p_k is the k-th prime."""
    primes = first_n_primes(count)
    return [(i + 1, p) for i, p in enumerate(primes)]


def format_points(points: list[tuple[int, int]]) -> str:
    return ", ".join(f"({a}, {b})" for a, b in points)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List the first n primes as (index, prime) points."
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=1000,
        metavar="N",
        help="how many primes (default: 1000)",
    )
    args = parser.parse_args()
    if args.count < 1:
        raise SystemExit("count must be at least 1")

    points = prime_points(args.count)
    print(format_points(points))


if __name__ == "__main__":
    main()
