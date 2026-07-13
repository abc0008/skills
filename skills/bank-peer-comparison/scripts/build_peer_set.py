#!/usr/bin/env python3
"""Build a comparable peer set for a target bank from the FDIC BankFind APIs.

Selection blends asset band + business model (hard gate) with Fed district /
region as a grouping and tie-breaker. Proximity (size + region + model) breaks
near ties. See references/peer_selection.md for the methodology.

Usage:
    python build_peer_set.py --target-cert 8728 [--count 11] [--out-dir .]
    python build_peer_set.py --target-name "Arvest Bank"
    python build_peer_set.py --target-cert 8728 --include-cert 110 5510 \
        --band-low 0.5 --band-high 2.0

Outputs: peer_set.csv and peer_set.json in --out-dir.
"""

from __future__ import annotations

import argparse
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

FDIC_INSTITUTIONS = "https://api.fdic.gov/banks/institutions"
USER_AGENT = "bank-peer-comparison/1.0"

SCREEN_FIELDS = [
    "NAME", "CERT", "STALP", "COUNTY", "FED", "FEDDESC", "ASSET", "DEP",
    "BKCLASS", "CALLFORM", "SPECGRP", "SPECGRPN", "QBPRCOML", "CB", "OFFDOM",
    "RSSDHCR", "NAMEHCR", "MUTUAL", "ACTIVE",
]

# Commercial-bank charter classes kept by default.
COMMERCIAL_BKCLASS = {"N", "SM", "NM", "SB"}

# Rough geographic adjacency of Fed districts for the region tie-break.
FED_NEIGHBORS = {
    "01": {"02"}, "02": {"01", "03"}, "03": {"02", "04", "05"},
    "04": {"03", "05", "07"}, "05": {"03", "04", "06"},
    "06": {"05", "08", "11"}, "07": {"04", "08", "09"},
    "08": {"06", "07", "10", "11"}, "09": {"07", "10"},
    "10": {"08", "09", "11"}, "11": {"06", "08", "10", "12"},
    "12": {"11"},
}


def fetch(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def institutions_url(filters: str, limit: int = 200, sort: str = "ASSET") -> str:
    params = urllib.parse.urlencode({
        "filters": filters,
        "fields": ",".join(SCREEN_FIELDS),
        "sort_by": sort,
        "sort_order": "DESC",
        "limit": str(limit),
        "format": "json",
    })
    return f"{FDIC_INSTITUTIONS}?{params}"


def get_one(filters: str) -> dict[str, Any] | None:
    data = fetch(institutions_url(filters, limit=10)).get("data", [])
    return data[0]["data"] if data else None


def search_by_name(name: str, limit: int = 10) -> list[dict[str, Any]]:
    """Fuzzy name search via the FDIC `search` param (filters require exact match).

    The `search` param can't be combined with an ACTIVE filter, and it returns
    current institutions, so we accept its results as-is and rely on the presence
    of recent assets to indicate an operating bank.
    """
    params = urllib.parse.urlencode({
        "search": f"NAME:{name}",
        "fields": ",".join(SCREEN_FIELDS),
        "limit": str(limit), "format": "json",
    })
    data = fetch(f"{FDIC_INSTITUTIONS}?{params}").get("data", [])
    return [d["data"] for d in data if float(d["data"].get("ASSET") or 0) > 0]


def resolve_target(cert: str | None, name: str | None) -> dict[str, Any]:
    if cert:
        rec = get_one(f"CERT:{cert} AND ACTIVE:1")
        if rec:
            return rec
        raise SystemExit(f"No active institution for CERT {cert}.")
    if name:
        # Try exact filter match first, then fuzzy search fallback.
        rec = get_one(f'NAME:"{name}" AND ACTIVE:1')
        if rec:
            return rec
        matches = search_by_name(name)
        if not matches:
            raise SystemExit(f'No active institution matching name "{name}".')
        if len(matches) > 1:
            # Multiple banks share/contain the name (e.g. "Cadence Bank" vs
            # "Cadence Bank, N.A."). Pick the largest by assets as the most
            # likely target, but report the alternatives so the user can correct.
            matches.sort(key=lambda r: float(r.get("ASSET") or 0), reverse=True)
            chosen = matches[0]
            alts = "; ".join(
                f"{m.get('NAME')} (CERT {m.get('CERT')}, "
                f"${float(m.get('ASSET') or 0)/1e6:.1f}B, {m.get('STALP')})"
                for m in matches[1:5]
            )
            print(f'NOTE: "{name}" matched {len(matches)} institutions. '
                  f"Using largest: {chosen.get('NAME')} (CERT {chosen.get('CERT')}). "
                  f"Other matches: {alts}. Re-run with --target-cert to pick a different one.")
            return chosen
        return matches[0]
    raise SystemExit("Provide --target-cert or --target-name.")


def region_distance(target_fed: str, cand_fed: str) -> float:
    if not target_fed or not cand_fed:
        return 1.0
    if target_fed == cand_fed:
        return 0.0
    if cand_fed in FED_NEIGHBORS.get(target_fed, set()):
        return 0.5
    return 1.0


def model_distance(t: dict[str, Any], c: dict[str, Any]) -> float:
    t_spec, c_spec = str(t.get("SPECGRP")), str(c.get("SPECGRP"))
    if t_spec == c_spec and str(c.get("BKCLASS")) in COMMERCIAL_BKCLASS:
        return 0.0
    if {t_spec, c_spec} <= {"4", "9"}:  # commercial vs large-diversified ~ compatible
        return 0.5
    return 1.0


def proximity(t: dict[str, Any], c: dict[str, Any]) -> float:
    t_assets = float(t["ASSET"]) or 1.0
    c_assets = float(c["ASSET"]) or 1.0
    size_d = abs(math.log(c_assets) - math.log(t_assets))
    region_d = region_distance(str(t.get("FED", "")).zfill(2), str(c.get("FED", "")).zfill(2))
    model_d = model_distance(t, c)
    return round(1.00 * size_d + 0.50 * region_d + 0.35 * model_d, 4)


def selection_reason(t: dict[str, Any], c: dict[str, Any]) -> str:
    ratio = float(c["ASSET"]) / (float(t["ASSET"]) or 1.0)
    same_region = str(c.get("FED")) == str(t.get("FED"))
    region = "in-region" if same_region else f"{c.get('STALP')} ({c.get('FEDDESC', 'other district')})"
    spec = c.get("SPECGRPN", "?")
    return f"{region} {spec.lower()} peer, {ratio:.2f}x assets"


def screen_candidates(target: dict[str, Any], band_low: float, band_high: float) -> list[dict[str, Any]]:
    t_assets = float(target["ASSET"])
    lo = int(t_assets * band_low)
    hi = int(t_assets * band_high)
    t_spec = str(target.get("SPECGRP"))
    # Keep target specialization, plus the compatible 4<->9 bridge.
    specs = {t_spec, "4", "9"} if t_spec in {"4", "9"} else {t_spec}
    spec_filter = " OR ".join(sorted(specs))
    bkclass_filter = " OR ".join(sorted(COMMERCIAL_BKCLASS))
    filters = (
        f"ACTIVE:1 AND ASSET:[{lo} TO {hi}] "
        f"AND SPECGRP:({spec_filter}) AND BKCLASS:({bkclass_filter})"
    )
    data = fetch(institutions_url(filters, limit=200)).get("data", [])
    out = []
    for item in data:
        rec = item["data"]
        if str(rec.get("CERT")) == str(target.get("CERT")):
            continue
        if str(rec.get("MUTUAL")) == "1" and str(target.get("MUTUAL")) != "1":
            continue
        out.append(rec)
    return out


FDIC_FINANCIALS = "https://api.fdic.gov/banks/financials"

# Financial fingerprint of an atypical (non-operating-commercial) bank: deposit
# sweep / trust / custody / brokerage-only institutions. These carry a commercial
# specialization code but distort a peer comparison. Detection is deliberately
# conservative: a merely lean/efficient commercial bank (low efficiency ratio but
# normal loans-to-deposits and real lending) is a GOOD peer and must not be
# dropped. A bank is treated as atypical only if it shows the structural sweep
# signature, not just one soft signal.
#
# Hard signals (each alone marks a non-operating bank):
#   - loans-to-deposits < 25  (a real lender deploys deposits into loans)
#   - uninsured-deposit share < 5  (sweep/custody deposits are insured-structured)
# Soft signal (only meaningful in combination):
#   - efficiency ratio < 30  (implausibly low for a full-service bank)
# Rule: drop if ANY hard signal fires, OR if the soft signal fires together with
# a moderately low loans-to-deposits (< 50), which separates true sweep/brokerage
# banks from merely efficient commercial banks.

def _hard_sweep(f: dict[str, Any]) -> list[str]:
    hits = []
    if f.get("LNLSDEPR") is not None and f["LNLSDEPR"] < 25:
        hits.append("loans_to_deposits_implausibly_low")
    if f.get("uninsured_pct") is not None and f["uninsured_pct"] < 5:
        hits.append("near_zero_uninsured_sweep_profile")
    return hits


def atypical_reason(f: dict[str, Any]) -> str | None:
    if f is None:
        return None
    hard = _hard_sweep(f)
    if hard:
        return ", ".join(hard)
    eff_low = f.get("eff") is not None and f["eff"] < 30
    ld_low = f.get("LNLSDEPR") is not None and f["LNLSDEPR"] < 50
    if eff_low and ld_low:
        return "implausible_efficiency_with_low_loan_deployment"
    return None



def fetch_fingerprints(certs: list[str]) -> dict[str, dict[str, Any]]:
    """One batched financials pull for all candidate CERTs; latest row each."""
    if not certs:
        return {}
    cert_filter = " OR ".join(f"CERT:{c}" for c in certs)
    params = urllib.parse.urlencode({
        "filters": cert_filter,
        "fields": "CERT,REPDTE,LNLSDEPR,NONIX,NIM,NONII,DEP,DEPUNINS,EEFFR",
        "sort_by": "REPDTE", "sort_order": "DESC",
        "limit": "400", "format": "json",
    })
    data = fetch(f"{FDIC_FINANCIALS}?{params}").get("data", [])
    latest: dict[str, dict[str, Any]] = {}
    for item in data:
        r = item["data"]
        c = str(r.get("CERT"))
        if c in latest:  # already have the most-recent (DESC sort)
            continue
        def fnum(k):
            v = r.get(k)
            try:
                return float(v) if v not in (None, "") else None
            except (TypeError, ValueError):
                return None
        nii, nir, nonix = fnum("NIM"), fnum("NONII"), fnum("NONIX")
        rev = (nii or 0) + (nir or 0)
        eff = fnum("EEFFR")
        if eff is None and rev:
            eff = nonix / rev * 100 if nonix is not None else None
        dep, unins = fnum("DEP"), fnum("DEPUNINS")
        latest[c] = {
            "LNLSDEPR": fnum("LNLSDEPR"),
            "eff": eff,
            "uninsured_pct": (unins / dep * 100) if (unins is not None and dep) else None,
        }
    return latest


def build_peer_set(
    target: dict[str, Any],
    count: int,
    band_low: float,
    band_high: float,
    include_certs: list[str],
    exclude_certs: list[str],
) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    t_assets = float(target["ASSET"])
    lo = int(t_assets * band_low)
    hi = int(t_assets * band_high)
    screen_filter = (
        f"ACTIVE:1 AND ASSET:[{lo} TO {hi}] AND SPECGRP:(...) AND BKCLASS:(...)"
    )

    forced: list[dict[str, Any]] = []
    for cert in include_certs:
        rec = get_one(f"CERT:{cert}")
        if rec:
            rec["_forced"] = True
            forced.append(rec)

    candidates = screen_candidates(target, band_low, band_high)
    candidates = [c for c in candidates if str(c.get("CERT")) not in set(exclude_certs)]
    forced_certs = {str(r.get("CERT")) for r in forced}
    candidates = [c for c in candidates if str(c.get("CERT")) not in forced_certs]

    for c in candidates:
        c["proximity_score"] = proximity(target, c)
    candidates.sort(key=lambda c: c["proximity_score"])

    # Financial-fingerprint outlier screen: drop sweep/trust/custody banks from
    # the default set. Batched single financials pull over the closest candidates
    # (cap the lookup to keep it fast; the closest banks are the ones we'd pick).
    lookup_pool = candidates[: max(count * 3, 30)]
    fingerprints = fetch_fingerprints([str(c.get("CERT")) for c in lookup_pool])
    dropped_outliers = []
    kept = []
    for c in candidates:
        fp = fingerprints.get(str(c.get("CERT")))
        reason = atypical_reason(fp) if fp else None
        if reason:
            c["_atypical_reason"] = reason
            dropped_outliers.append(c)
        else:
            kept.append(c)
    candidates = kept

    remaining = max(0, count - len(forced))
    chosen = forced + candidates[:remaining]

    rows = []
    for c in chosen:
        c.setdefault("proximity_score", proximity(target, c))
        rows.append({
            "cert": str(c.get("CERT")),
            "name": c.get("NAME"),
            "state": c.get("STALP"),
            "fed_district": str(c.get("FED", "")).zfill(2),
            "fed_district_name": c.get("FEDDESC"),
            "assets_$000": float(c.get("ASSET") or 0),
            "deposits_$000": float(c.get("DEP") or 0),
            "branches": int(c.get("OFFDOM") or 0),
            "specialization_code": c.get("SPECGRP"),
            "specialization": c.get("SPECGRPN"),
            "charter_class": c.get("BKCLASS"),
            "call_form": c.get("CALLFORM"),
            "holdco_rssd": c.get("RSSDHCR"),
            "holdco_name": c.get("NAMEHCR"),
            "proximity_score": c.get("proximity_score"),
            "forced_by_user": bool(c.get("_forced")),
            "selection_reason": "user-supplied" if c.get("_forced") else selection_reason(target, c),
        })

    outlier_rows = [{
        "cert": str(c.get("CERT")), "name": c.get("NAME"), "state": c.get("STALP"),
        "assets_$000": float(c.get("ASSET") or 0),
        "specialization": c.get("SPECGRPN"),
        "dropped_reason": c.get("_atypical_reason"),
    } for c in dropped_outliers[: count]]
    return rows, screen_filter, outlier_rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a comparable bank peer set from FDIC data.")
    ap.add_argument("--target-cert")
    ap.add_argument("--target-name")
    ap.add_argument("--count", type=int, default=11)
    ap.add_argument("--band-low", type=float, default=0.5)
    ap.add_argument("--band-high", type=float, default=2.0)
    ap.add_argument("--include-cert", nargs="*", default=[])
    ap.add_argument("--exclude-cert", nargs="*", default=[])
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()

    target = resolve_target(args.target_cert, args.target_name)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows, screen_filter, outliers = build_peer_set(
        target, args.count, args.band_low, args.band_high,
        [str(c) for c in args.include_cert], [str(c) for c in args.exclude_cert],
    )

    target_row = {
        "cert": str(target.get("CERT")),
        "name": target.get("NAME"),
        "state": target.get("STALP"),
        "fed_district": str(target.get("FED", "")).zfill(2),
        "fed_district_name": target.get("FEDDESC"),
        "assets_$000": float(target.get("ASSET") or 0),
        "specialization": target.get("SPECGRPN"),
        "charter_class": target.get("BKCLASS"),
        "holdco_rssd": target.get("RSSDHCR"),
        "holdco_name": target.get("NAMEHCR"),
        "is_target": True,
    }

    import csv
    cols = list(rows[0].keys()) if rows else []
    with (out_dir / "peer_set.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    (out_dir / "peer_set.json").write_text(json.dumps({
        "target": target_row,
        "band_low": args.band_low,
        "band_high": args.band_high,
        "requested_count": args.count,
        "screen_filter": screen_filter,
        "peers": rows,
        "dropped_outliers": outliers,
    }, indent=2) + "\n")

    print(f"Target: {target_row['name']} (CERT {target_row['cert']}, "
          f"${target_row['assets_$000']/1e6:.1f}B, {target_row['specialization']})")
    print(f"Selected {len(rows)} peers:")
    for r in rows:
        flag = " [user]" if r["forced_by_user"] else ""
        print(f"  {r['cert']:>6}  {str(r['name'])[:32]:<33} {r['state']}  "
              f"${r['assets_$000']/1e6:>5.1f}B  score={r['proximity_score']:.2f}{flag}")
    if outliers:
        print(f"Dropped {len(outliers)} atypical bank(s) from the default set "
              f"(force back with --include-cert if wanted):")
        for o in outliers:
            print(f"  {o['cert']:>6}  {str(o['name'])[:32]:<33} {o['state']}  "
                  f"— {o['dropped_reason']}")
    print(f"Wrote {out_dir/'peer_set.csv'} and {out_dir/'peer_set.json'}")


if __name__ == "__main__":
    main()
