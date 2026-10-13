"""In-process federated-style Cox PH estimation with stratification and Breslow ties.

Site objects retain individual patient rows. Only event schedules and aggregated
risk-set moments are transferred to the coordinator. Aggregation is NOT secure
multiparty computation, differential privacy, or a production network protocol.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class CoxResult:
    coefficients: tuple[float, ...]
    hazard_ratios: tuple[float, ...]
    log_partial_likelihood: float
    converged: bool
    iterations: int
    events: int
    observations: int
    sites: int
    strata: int

    def to_dict(self) -> dict:
        return {
            "coefficients": list(self.coefficients),
            "hazard_ratios": list(self.hazard_ratios),
            "log_partial_likelihood": self.log_partial_likelihood,
            "converged": self.converged,
            "iterations": self.iterations,
            "events": self.events,
            "observations": self.observations,
            "sites": self.sites,
            "strata": self.strata,
            "ties": "breslow",
            "privacy": "Aggregates are not differentially private or cryptographically protected",
        }


class CoxSite:
    """Local records. Only aggregate statistics are exposed through methods."""

    def __init__(self, records: Iterable[Mapping]):
        self._rows = []
        self.features = None
        for record in records:
            time = float(record["time"])
            if not math.isfinite(time) or time < 0:
                raise ValueError("time must be finite and non-negative")
            event = record["event"]
            if event not in (0, 1, False, True):
                raise ValueError("event must be 0 or 1")
            x = tuple(float(value) for value in record["covariates"])
            if not x or not all(math.isfinite(value) for value in x):
                raise ValueError("covariates must be nonempty and finite")
            if self.features is None:
                self.features = len(x)
            if len(x) != self.features:
                raise ValueError("inconsistent covariate dimensionality")
            stratum = str(record.get("stratum", "all"))
            if not stratum:
                raise ValueError("stratum must not be empty")
            self._rows.append((time, int(event), x, stratum))
        if not self._rows:
            raise ValueError("each site requires at least one record")

    @property
    def observations(self):
        return len(self._rows)

    def event_counts(self):
        counts = {}
        for time, event, _, stratum in self._rows:
            if event:
                key = (stratum, time)
                counts[key] = counts.get(key, 0) + 1
        return counts

    def max_risk_score(self, stratum: str, time: float, beta: Sequence[float]):
        scores = (sum(a * b for a, b in zip(x, beta))
                  for t, _, x, s in self._rows if s == stratum and t >= time)
        return max(scores, default=-math.inf)

    def moments(self, stratum: str, time: float, beta: Sequence[float], offset: float):
        p = self.features
        s0, s1, s2 = 0.0, [0.0] * p, [[0.0] * p for _ in range(p)]
        event_x = [0.0] * p
        event_eta = 0.0
        for t, event, x, s in self._rows:
            if s != stratum:
                continue
            eta = sum(a * b for a, b in zip(x, beta))
            if t >= time:
                w = math.exp(eta - offset)
                s0 += w
                for j in range(p):
                    s1[j] += w * x[j]
                    for k in range(p):
                        s2[j][k] += w * x[j] * x[k]
            if t == time and event:
                event_eta += eta
                for j in range(p):
                    event_x[j] += x[j]
        return s0, s1, s2, event_x, event_eta


def _solve(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    """Partial-pivot Gaussian elimination of the information system."""
    n = len(rhs)
    aug = [list(matrix[i]) + [rhs[i]] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-12:
            raise ValueError("singular information matrix; remove collinear variables or use ridge")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = aug[col][col]
        for j in range(col, n + 1):
            aug[col][j] /= scale
        for row in range(col + 1, n):
            factor = aug[row][col]
            for j in range(col, n + 1):
                aug[row][j] -= factor * aug[col][j]
    result = [0.0] * n
    for i in range(n - 1, -1, -1):
        result[i] = aug[i][n] - sum(aug[i][j] * result[j] for j in range(i + 1, n))
    return result


def fit_federated_cox(sites: Sequence[CoxSite], *, max_iterations: int = 100,
                      tolerance: float = 1e-8, ridge: float = 0.0) -> CoxResult:
    """Fit a stratified Cox model from site aggregates; in-process prototype only."""
    if not sites:
        raise ValueError("provide at least one site")
    if not isinstance(max_iterations, int) or max_iterations < 1:
        raise ValueError("max_iterations must be a positive integer")
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance must be positive and finite")
    if not math.isfinite(ridge) or ridge < 0:
        raise ValueError("ridge must be non-negative and finite")
    p = sites[0].features
    if any(site.features != p for site in sites):
        raise ValueError("all sites must use the same number and order of covariates")
    schedule = {}
    for site in sites:
        for key, count in site.event_counts().items():
            schedule[key] = schedule.get(key, 0) + count
    if not schedule:
        raise ValueError("at least one observed event is required")
    events = sum(schedule.values())
    event_times = sorted(schedule)
    beta = [0.0] * p

    def objective(b):
        loglik, gradient, information = 0.0, [0.0] * p, [[0.0] * p for _ in range(p)]
        for (stratum, time) in event_times:
            d = schedule[(stratum, time)]
            offset = max(site.max_risk_score(stratum, time, b) for site in sites)
            s0, s1, s2 = 0.0, [0.0] * p, [[0.0] * p for _ in range(p)]
            event_x, event_eta = [0.0] * p, 0.0
            for site in sites:
                a0, a1, a2, ex, ee = site.moments(stratum, time, b, offset)
                s0 += a0
                event_eta += ee
                for j in range(p):
                    s1[j] += a1[j]
                    event_x[j] += ex[j]
                    for k in range(p):
                        s2[j][k] += a2[j][k]
            if s0 <= 0 or not math.isfinite(s0):
                raise ValueError("invalid risk set")
            loglik += event_eta - d * (offset + math.log(s0))
            for j in range(p):
                mean_j = s1[j] / s0
                gradient[j] += event_x[j] - d * mean_j
                for k in range(p):
                    information[j][k] += d * (s2[j][k] / s0 - mean_j * s1[k] / s0)
        loglik -= 0.5 * ridge * sum(x*x for x in b)
        for j in range(p):
            gradient[j] -= ridge*b[j]
            information[j][j] += ridge
        return loglik, gradient, information

    converged = False
    iterations = 0
    for iteration in range(1, max_iterations + 1):
        value, gradient, information = objective(beta)
        _solve(information, [0.0] * p)  # Reject unidentifiable models even when score is zero.
        if max(abs(x) for x in gradient) < tolerance:
            converged = True
            iterations = iteration - 1
            break
        step = _solve(information, gradient)
        scale = 1.0
        candidate = beta
        for _ in range(30):
            candidate = [a + scale*b for a, b in zip(beta, step)]
            trial, _, _ = objective(candidate)
            if math.isfinite(trial) and trial >= value - 1e-12:
                break
            scale /= 2
        else:
            iterations = iteration
            break
        beta = candidate
        iterations = iteration
        if max(abs(scale*s) for s in step) < tolerance:
            converged = True
            break
    value, _, _ = objective(beta)
    hazard_ratios = tuple(math.exp(x) if x < 709 else math.inf for x in beta)
    return CoxResult(tuple(beta), hazard_ratios, value, converged, iterations,
                     events, sum(site.observations for site in sites), len(sites),
                     len({key[0] for key in schedule}))
