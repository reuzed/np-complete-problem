"""
Set cover: universe U, family of subsets S_i with optional costs c_i.

Pure Python: weighted greedy (log-factor approximation) and exact bitmask
enumeration for small instances. ILP: exact optimum via PuLP + CBC.
"""

from __future__ import annotations

from typing import Hashable, Iterable, Sequence, TypeVar

try:
    from pulp import LpMinimize, LpProblem, LpVariable, PULP_CBC_CMD, lpSum
except ImportError:  # pragma: no cover - optional until pulp installed
    LpProblem = None  # type: ignore[misc, assignment]

T = TypeVar("T", bound=Hashable)


def greedy_set_cover(
    universe: Iterable[T],
    subsets: Sequence[set[T]],
    costs: Sequence[float] | None = None,
) -> list[int]:
    """
    Weighted greedy: repeatedly pick a set minimizing cost / newly covered elements.
    Polynomial-time; solution cost is at most H(|U|) times optimal for unit costs.

    Returns indices of chosen sets.
    """
    u = set(universe)
    if not u:
        return []

    n = len(subsets)
    costs = list(costs) if costs is not None else [1.0] * n
    if len(costs) != n:
        raise ValueError("costs must have the same length as subsets")

    uncovered = set(u)
    chosen: list[int] = []

    while uncovered:
        best_i: int | None = None
        best_ratio = float("inf")

        for i in range(n):
            new = subsets[i] & uncovered
            if not new:
                continue
            ratio = costs[i] / len(new)
            if ratio < best_ratio:
                best_ratio = ratio
                best_i = i

        if best_i is None:
            raise ValueError("infeasible: some universe element is not covered by any set")

        chosen.append(best_i)
        uncovered -= subsets[best_i]

    return chosen


def exact_set_cover_bitmask(
    universe: Iterable[T],
    subsets: Sequence[set[T]],
    costs: Sequence[float] | None = None,
) -> list[int] | None:
    """
    Exact minimum-cost set cover by enumerating all 2^n subset masks.
    Feasible only for n = len(subsets) up to about 25–28 in practice.

    Returns indices of an optimal cover, or None if infeasible.
    """
    u = set(universe)
    n = len(subsets)
    costs = list(costs) if costs is not None else [1.0] * n
    if len(costs) != n:
        raise ValueError("costs must have the same length as subsets")

    best_mask: int | None = None
    best_cost = float("inf")

    for mask in range(1 << n):
        covered: set[T] = set()
        total = 0.0
        for i in range(n):
            if (mask >> i) & 1:
                covered |= subsets[i]
                total += costs[i]
        if covered >= u and total < best_cost:
            best_cost = total
            best_mask = mask

    if best_mask is None:
        return None
    return [i for i in range(n) if (best_mask >> i) & 1]


def ilp_set_cover(
    universe: Iterable[T],
    subsets: Sequence[set[T]],
    costs: Sequence[float] | None = None,
) -> list[int]:
    """
    Integer linear program (binary x_i): minimize sum c_i x_i subject to
    for each element e, sum_{i: e in S_i} x_i >= 1.

    Requires: pip install pulp
    """
    if LpProblem is None:
        raise ImportError("ilp_set_cover requires the 'pulp' package: pip install pulp")

    u = list(dict.fromkeys(universe))  # stable unique elements
    n = len(subsets)
    costs = list(costs) if costs is not None else [1.0] * n
    if len(costs) != n:
        raise ValueError("costs must have the same length as subsets")

    prob = LpProblem("setcover", LpMinimize)
    x = [LpVariable(f"x{i}", cat="Binary") for i in range(n)]
    prob += lpSum(costs[i] * x[i] for i in range(n))

    for e in u:
        idxs = [i for i, s in enumerate(subsets) if e in s]
        if not idxs:
            raise ValueError(f"element {e!r} is not contained in any set")
        prob += lpSum(x[i] for i in idxs) >= 1

    prob.solve(PULP_CBC_CMD(msg=0))
    return [i for i in range(n) if x[i].value() is not None and x[i].value() > 0.5]


if __name__ == "__main__":
    # Example: U = {1,2,3,4}, sets {1,2}, {2,3}, {3,4}, {1,4}
    U = {1, 2, 3, 4}
    S = [{1, 2}, {2, 3}, {3, 4}, {1, 4}]
    c = [2.0, 1.0, 1.0, 2.0]

    g = greedy_set_cover(U, S, c)
    print("greedy indices:", g, "cost:", sum(c[i] for i in g))

    e = exact_set_cover_bitmask(U, S, c)
    print("exact (bitmask) indices:", e, "cost:", sum(c[i] for i in e) if e else None)

    opt = ilp_set_cover(U, S, c)
    print("ILP indices:", opt, "cost:", sum(c[i] for i in opt))
