#!/usr/bin/env python3
"""
Enumerate lines y = m x + c (in rational slope–intercept form) that pass through
at least two prime lattice points (k, p_k). Each line is represented by a
normalized integer triple (A, B, C) with A x + B y + C = 0.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from fractions import Fraction
from math import gcd

from primes import prime_points


def normalize_line(a: int, b: int, c: int) -> tuple[int, int, int]:
    """Canonical sign/magnitude for integer line A x + B y + C = 0."""
    g = gcd(gcd(abs(a), abs(b)), abs(c))
    if g:
        a, b, c = a // g, b // g, c // g
    for v in (a, b, c):
        if v != 0:
            if v < 0:
                a, b, c = -a, -b, -c
            break
    return (a, b, c)


def line_through(
    p1: tuple[int, int], p2: tuple[int, int]
) -> tuple[int, int, int]:
    """Unique normalized (A, B, C) for the infinite line through two distinct points."""
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        raise ValueError("duplicate point")
    if dx == 0:
        return normalize_line(1, 0, -x1)
    g = gcd(abs(dx), abs(dy))
    dx //= g
    dy //= g
    if dx < 0:
        dx, dy = -dx, -dy
    a = dy
    b = -dx
    c = dx * y1 - dy * x1
    return normalize_line(a, b, c)


def point_on_line(x: int, y: int, line: tuple[int, int, int]) -> bool:
    a, b, c = line
    return a * x + b * y + c == 0


def prime_lines_and_points(
    count: int,
) -> tuple[list[tuple[int, int]], dict[tuple[int, int, int], set[int]]]:
    """
    Return (points, line_map).

    points[i] = (i+1, p_{i+1}). line_map[line] = set of indices i with points[i] on line.
    Only lines that contain at least two prime points appear.
    """
    points = prime_points(count)
    n = len(points)
    acc: dict[tuple[int, int, int], set[int]] = defaultdict(set)
    for i in range(n):
        for j in range(i + 1, n):
            key = line_through(points[i], points[j])
            acc[key].add(i)
            acc[key].add(j)
    return points, dict(acc)


def lines_with_point_indices(
    count: int,
) -> tuple[list[tuple[int, int]], list[tuple[tuple[int, int, int], set[int]]]]:
    """
    Same as prime_lines_and_points but returns a list of (line, indices) sorted by line key.
    """
    points, m = prime_lines_and_points(count)
    items = sorted(m.items(), key=lambda kv: kv[0])
    return points, items


def format_line_human(line: tuple[int, int, int], points: list[tuple[int, int]]) -> str:
    a, b, c = line
    idxs = [i for i, (x, y) in enumerate(points) if point_on_line(x, y, line)]
    pts_str = ", ".join(f"({points[i][0]}, {points[i][1]})" for i in idxs)
    if b == 0:
        eq = f"x = {Fraction(-c, a)}"
    elif a == 0:
        eq = f"y = {Fraction(-c, b)}"
    else:
        m = Fraction(-a, b)
        y0 = Fraction(-c, b)
        eq = f"y = ({m}) x + ({y0})"
    return f"{a}x + {b}y + {c} = 0  →  {eq}  |  points: [{pts_str}]"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List lines through two or more prime points (k, p_k)."
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=20,
        metavar="N",
        help="how many primes / points (default: 20)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON: lines as A,B,C and lists of point indices",
    )
    args = parser.parse_args()
    if args.count < 2:
        raise SystemExit("need at least 2 primes to form lines")

    points, items = lines_with_point_indices(args.count)

    if args.json:
        payload = {
            "points": [{"index": i, "x": x, "y": y} for i, (x, y) in enumerate(points)],
            "lines": [
                {
                    "A": line[0],
                    "B": line[1],
                    "C": line[2],
                    "point_indices": sorted(list(idxs)),
                }
                for line, idxs in items
            ],
            "num_lines": len(items),
        }
        print(json.dumps(payload, indent=2))
        return

    print(f"Prime points (n={args.count}): {len(points)} points, {len(items)} distinct lines with ≥2 points\n")
    for line, idxs in items:
        print(format_line_human(line, points))
        print()


if __name__ == "__main__":
    main()
