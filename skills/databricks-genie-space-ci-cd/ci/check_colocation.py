#!/usr/bin/env python3
"""
check_colocation.py — L1 PREVENTIVE GATE (runs on every pull request).

If a PR changes a model file but does NOT also change the metric view(s) and/or
Genie space(s) that depend on it, this exits non-zero and BLOCKS THE MERGE —
forcing the author to consciously re-review the dependent definition. This is
the direct equivalent of Anthropic's "model change must touch its doc" CI hook.

LOGIC (preserve if refactoring):
  1. config.yaml -> dependency map (models -> views -> spaces).
  2. git -> files changed in this PR vs the target branch.
  3. model changed but its metric view not changed -> violation.
  4. metric view OR its models changed but the dependent space not changed
     -> violation.
  5. violations -> print + exit 1; else exit 0.

ESCAPE HATCH (audited): if a model change is genuinely irrelevant to a dependent
definition, the author adds  `drift-ack: <logical_name> <reason>`  to the PR
description. Acknowledged names are treated as satisfied. The ack is in git
history, so a human still made the call.

Exit codes: 0 clean | 1 violations | 2 setup/config error.
"""

from __future__ import annotations

import argparse
import re
import sys

import databricks_helpers as h
from _core import ConfigError, get_logger

log = get_logger("drift.L1")

ACK_RE = re.compile(r"drift-ack:\s*([A-Za-z0-9_\-]+)", re.I)


def parse_acks(ack_text: str) -> set[str]:
    return {m.group(1).strip() for m in ACK_RE.finditer(ack_text or "")}


def find_violations(cfg: dict, changed: set[str], acks: set[str]) -> list[str]:
    """Pure function (no I/O) so it is fully unit-testable. Returns a list of
    human-readable violation messages."""
    violations: list[str] = []

    # Seam 1: model -> metric view
    for view_name, spec in (cfg.get("metric_views") or {}).items():
        spec = spec or {}
        view_file = f"metric_views/{view_name}{h.VIEW_SUFFIX}"
        touched = set(spec.get("depends_on_models") or []) & changed
        if touched and view_file not in changed and view_name not in acks:
            violations.append(
                f"METRIC VIEW '{view_name}' may be stale.\n"
                f"    changed model(s): {', '.join(sorted(touched))}\n"
                f"    but {view_file} was NOT updated in this PR.\n"
                f"    -> Update the metric view, or add "
                f"'drift-ack: {view_name} <reason>' to the PR description.")

    # Seam 2: metric view / model -> genie space
    changed_view_names = {h.logical_name(f) for f in changed if f.endswith(h.VIEW_SUFFIX)}
    for space_name, spec in (cfg.get("genie_spaces") or {}).items():
        spec = spec or {}
        space_file = f"genie_spaces/{space_name}{h.SPACE_SUFFIX}"
        trig_views = set(spec.get("depends_on_metric_views") or []) & changed_view_names
        trig_models = set(spec.get("depends_on_models") or []) & changed
        if (trig_views or trig_models) and space_file not in changed and space_name not in acks:
            reasons = []
            if trig_views:
                reasons.append(f"metric view(s) changed: {', '.join(sorted(trig_views))}")
            if trig_models:
                reasons.append(f"model(s) changed: {', '.join(sorted(trig_models))}")
            violations.append(
                f"GENIE SPACE '{space_name}' may be stale.\n"
                f"    {'; '.join(reasons)}\n"
                f"    but {space_file} was NOT updated in this PR.\n"
                f"    -> Re-export the space after review, or add "
                f"'drift-ack: {space_name} <reason>' to the PR description.")

    return violations


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="L1 colocation gate")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--ack-text", default="")
    args = ap.parse_args(argv)

    cfg = h.load_config()  # validates; raises ConfigError on bad setup
    changed = set(h.changed_files(args.base))
    acks = parse_acks(args.ack_text)

    if not changed:
        log.info("no changed files vs %s — nothing to check.", args.base)
        return 0

    log.info("checking %d changed file(s) vs %s", len(changed), args.base)
    for f in sorted(changed):
        log.debug("  changed: %s", f)
    if acks:
        log.info("drift-acks present for: %s", ", ".join(sorted(acks)))

    violations = find_violations(cfg, changed, acks)
    if violations:
        log.error("L1 FAILED — %d colocation violation(s):", len(violations))
        for i, v in enumerate(violations, 1):
            print(f"\n[{i}] {v}")
        print("\n" + "=" * 70)
        print("Fix: move the dependent file(s) in THIS PR, or add an audited "
              "drift-ack line to the PR description.")
        return 1

    log.info("L1 PASSED — every changed model carried its dependent "
             "metric views / Genie spaces.")
    return 0


def _entry() -> int:
    try:
        return main()
    except ConfigError as e:
        log.error("setup/config error: %s", e)
        return 2
    except Exception as e:  # never silently pass the gate on an unexpected crash
        log.error("unexpected error (failing safe): %s", e)
        return 2


if __name__ == "__main__":
    sys.exit(_entry())
