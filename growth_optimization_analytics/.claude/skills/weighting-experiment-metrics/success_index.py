#!/usr/bin/env python3
"""Exact calculations for the weighting-experiment-metrics skill.

Executable mirror of reference.md §2 (the index), §2.1 (aggregate vs unit-level +
two-sample t-test) and §7 (the deployment gate). Pure stdlib — no install.

Import the functions, or run the CLI:
    python success_index.py config.json      # or: cat config.json | python success_index.py
    python success_index.py --self-check
"""
import json
import math
import sys

# ---- numerics: regularized incomplete beta -> two-sided Student-t p-value ----
# Lentz continued fraction for I_x(a,b) (Numerical Recipes `betai`). Pure Python
# so the t-test p-value is exact without scipy.

def _betacf(a, b, x):
    MAXIT, EPS, FPMIN = 300, 3e-16, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = FPMIN if abs(d) < FPMIN else d
        c = 1.0 + aa / c
        c = FPMIN if abs(c) < FPMIN else c
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = FPMIN if abs(d) < FPMIN else d
        c = 1.0 + aa / c
        c = FPMIN if abs(c) < FPMIN else c
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h


def _betai(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def _t_p_two(t, df):
    """P(|T| > |t|) for Student-t with df degrees of freedom."""
    return _betai(df / 2.0, 0.5, df / (df + t * t))


# ---- the index (reference.md §2 / §2.1) ----

def compute_index(driver_weights, penalty_weights, deltas):
    """Σ wᵢ·Δ(driver) − Σ pⱼ·Δ(drag). Missing metric = 0.0 (everything-else-flat)."""
    pos = sum(w * deltas.get(k, 0.0) for k, w in driver_weights.items())
    neg = sum(p * deltas.get(k, 0.0) for k, p in penalty_weights.items())
    return pos - neg


def user_scores(rows, driver_weights, penalty_weights):
    """Per-user index scores — the same formula applied to each user's metrics."""
    return [compute_index(driver_weights, penalty_weights, row) for row in rows]


# ---- statistical validation (reference.md §2.1) ----

def _mean(v):
    return sum(v) / len(v)


def _var(v):
    m = _mean(v)
    return sum((x - m) ** 2 for x in v) / (len(v) - 1)


def welch_ttest(control, treatment):
    """Welch (unequal-variance) two-sample t-test. Returns (t, df, p_two_sided).

    t sign follows treatment − control (positive = treatment scored higher).
    """
    if len(control) < 2 or len(treatment) < 2:
        raise ValueError("need >= 2 observations per arm for a t-test")
    na, nb = len(control), len(treatment)
    va, vb = _var(control), _var(treatment)
    diff = _mean(treatment) - _mean(control)
    se2 = va / na + vb / nb
    if se2 == 0.0:  # both arms constant
        if diff == 0.0:
            return 0.0, float("nan"), 1.0
        return math.copysign(float("inf"), diff), float("nan"), 0.0
    se = math.sqrt(se2)
    t = diff / se
    df = se2 ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    return t, df, _t_p_two(t, df)


def validate_weights(driver_weights, penalty_weights, floor=1.0, tol=1e-9):
    """Method invariants: Σw = 1.0, drivers non-negative, penalties >= floor."""
    problems = []
    s = sum(driver_weights.values())
    if abs(s - 1.0) > tol:
        problems.append(f"driver weights sum to {s:.6g}, must be 1.0")
    for k, w in driver_weights.items():
        if w < 0:
            problems.append(f"driver weight {k}={w} is negative")
    for k, p in penalty_weights.items():
        if p < floor:
            problems.append(f"penalty {k}={p} below asymmetry floor {floor}")
    return problems


# ---- the deployment gate (reference.md §7) ----

def gate(value, p=None, alpha=0.05):
    """value>0 & significant -> DEPLOY; <=0 -> REJECT; >0 & not sig -> INCONCLUSIVE.

    p=None is the aggregate-only path: DEPLOY on sign but flagged directional
    (significance unverified).
    """
    if value <= 0:
        return {"deploy": False, "verdict": "REJECT",
                "reason": f"index {value:.6g} <= 0"}
    if p is None:
        return {"deploy": True, "verdict": "DEPLOY",
                "reason": "positive index; DIRECTIONAL only — significance unverified "
                          "(no per-user data); confirm with a two-sample t-test before rollout"}
    if p < alpha:
        return {"deploy": True, "verdict": "DEPLOY",
                "reason": f"positive index, significant (p={p:.4g} < {alpha})"}
    return {"deploy": False, "verdict": "INCONCLUSIVE",
            "reason": f"positive index but not significant (p={p:.4g} >= {alpha}); "
                      "extend the test — not a true negative"}


# ---- CLI ----

def _evaluate(config):
    dw, pw = config["driver_weights"], config["penalty_weights"]
    out = {"weight_problems": validate_weights(dw, pw)}
    if "aggregate_deltas" in config:
        value = compute_index(dw, pw, config["aggregate_deltas"])
        out["mode"] = "aggregate"
        out["value"] = round(value, 6)
        out.update(gate(value))
    elif "control" in config and "treatment" in config:
        cs = user_scores(config["control"], dw, pw)
        ts = user_scores(config["treatment"], dw, pw)
        value = _mean(ts) - _mean(cs)
        t, df, p = welch_ttest(cs, ts)
        out["mode"] = "unit-level"
        out["value"] = round(value, 6)
        out["t"] = round(t, 6)
        out["df"] = round(df, 6) if math.isfinite(df) else None
        out["p"] = round(p, 8)
        out.update(gate(value, p))
    else:
        raise ValueError("config needs either 'aggregate_deltas' or 'control'+'treatment'")
    return out


def _self_check():
    ex1 = compute_index({"acq": 0.2, "exp": 0.2, "onb": 0.6},
                        {"attr": 2.0, "bad": 1.0, "fric": 2.5},
                        {"acq": 3, "onb": 15, "fric": 1})
    assert abs(ex1 - 7.1) < 1e-9, ex1
    assert gate(ex1)["verdict"] == "DEPLOY" and gate(ex1)["deploy"]

    ex2 = compute_index({"acq": 0.2, "exp": 0.5, "onb": 0.3},
                        {"attr": 2.0, "bad": 3.0, "fric": 1.0},
                        {"exp": 14, "bad": 4, "fric": 2})
    assert abs(ex2 - (-7.0)) < 1e-9, ex2
    assert gate(ex2)["verdict"] == "REJECT" and not gate(ex2)["deploy"]

    good = {"a": 0.5, "b": 0.2, "c": 0.3}
    assert validate_weights(good, {"x": 1.0, "y": 2.5}) == []
    bad = validate_weights({"a": 0.5, "b": 0.4}, {"x": 0.5})
    assert any("sum" in m for m in bad) and any("floor" in m for m in bad), bad

    ctrl = [0, 0, 1, 0, 2, 0, 1, 0, 0, 1, 0, 0, 3, 0, 1]
    treat = [1, 2, 0, 3, 2, 1, 4, 0, 2, 3, 1, 2, 0, 3, 2]
    t, df, p = welch_ttest(ctrl, treat)
    assert abs(t - 2.87941) < 1e-4, t
    assert abs(df - 25.87076) < 1e-4, df
    assert abs(p - 0.0078935) < 1e-4, p
    assert abs(_t_p_two(1.959964, 1e6) - 0.05) < 1e-4  # ~z at 95%

    assert gate(5.0, p=0.21)["verdict"] == "INCONCLUSIVE"
    assert gate(5.0, p=0.01)["verdict"] == "DEPLOY"
    print("OK")


def main(argv):
    if "--self-check" in argv:
        _self_check()
        return
    raw = open(argv[1]).read() if len(argv) > 1 else sys.stdin.read()
    print(json.dumps(_evaluate(json.loads(raw)), indent=2))


if __name__ == "__main__":
    main(sys.argv)
