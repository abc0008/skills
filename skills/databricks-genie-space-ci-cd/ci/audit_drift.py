#!/usr/bin/env python3
"""
audit_drift.py — L2 DETECTIVE AUDIT (nightly).

For every managed Genie space + metric view, fetch the LIVE definition,
normalize it, and compare to the committed repo blueprint. A difference means
someone edited the live object OUTSIDE the pipeline (a UI edit) — i.e. workspace
and repo have drifted. L1 cannot see this (no PR to gate); L2 is the backstop.

On drift: print a diff, optionally open an Azure DevOps work item for the
governance team, and exit non-zero. It does NOT auto-revert or auto-edit — a
human decides whether to redeploy the repo blueprint or capture the intended
edit via a PR. An agent may draft the corrective PR; a human approves it.

Exit codes: 0 match | 2 setup/config | 3 drift found | 7 partial (some objects
errored AND no drift among the rest — investigate the errors).
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import sys

import yaml

import databricks_helpers as h
from _core import (ConfigError, DriftDefenseError, PermanentError,
                   TransientError, get_logger)

log = get_logger("drift.L2")


def unified_diff(repo_text: str, live_text: str, label: str) -> str:
    return "".join(difflib.unified_diff(
        repo_text.splitlines(keepends=True),
        live_text.splitlines(keepends=True),
        fromfile=f"repo/{label}", tofile=f"live/{label}"))


def open_azure_workitem(title: str, body: str) -> bool:
    """Create an Azure DevOps work item. Returns True on success. No-op (returns
    False) if the AZDO_* env isn't set, so local runs never crash."""
    org = os.environ.get("AZDO_ORG_URL")
    project = os.environ.get("AZDO_PROJECT")
    pat = os.environ.get("AZDO_PAT")
    if not all([org, project, pat]):
        log.warning("AZDO_* env not set; skipping work-item creation.")
        return False
    import base64
    import requests
    wit = os.environ.get("AZDO_WORKITEM_TYPE", "Issue")  # >>> ADAPT process template
    url = f"{org}/{project}/_apis/wit/workitems/${wit}?api-version=7.1"
    auth = base64.b64encode(f":{pat}".encode()).decode()
    patch = [
        {"op": "add", "path": "/fields/System.Title", "value": title[:255]},
        {"op": "add", "path": "/fields/System.Description",
         "value": body.replace("\n", "<br>")},
    ]
    area = os.environ.get("AZDO_AREA_PATH")
    if area:
        patch.append({"op": "add", "path": "/fields/System.AreaPath", "value": area})
    try:
        r = requests.post(url, headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json-patch+json"},
            data=json.dumps(patch), timeout=60)
    except requests.RequestException as e:
        log.error("work-item POST failed (network): %s", e)
        return False
    if r.status_code < 300:
        log.info("opened Azure DevOps work item #%s", r.json().get("id"))
        return True
    log.error("work-item creation failed (%s): %s", r.status_code, r.text[:300])
    return False


def audit_spaces(cfg, env, adapter):
    """Yield (status, name, detail) where status in {ok, drift, error, skip}."""
    for name, spec in (cfg.get("genie_spaces") or {}).items():
        spec = spec or {}
        bp = h.GENIE_SPACES_DIR / f"{name}{h.SPACE_SUFFIX}"
        if not bp.exists():
            yield "skip", name, f"no blueprint at {bp} (export it first)"
            continue
        try:
            space_id = h.get_space_id(cfg, name, env)
            repo_obj = h.normalize_space(json.loads(bp.read_text()), cfg)
            live_raw, _etag = adapter.export_space(space_id)
            live_obj = h.normalize_space(live_raw, cfg)
            rt, lt = h.canonical_json(repo_obj), h.canonical_json(live_obj)
            if rt != lt:
                yield "drift", name, unified_diff(rt, lt, f"{name}{h.SPACE_SUFFIX}")
            else:
                yield "ok", name, ""
        except (ConfigError, PermanentError, TransientError, DriftDefenseError) as e:
            yield "error", name, str(e)


def audit_metric_views(cfg, adapter):
    for name in (cfg.get("metric_views") or {}):
        bp = h.METRIC_VIEWS_DIR / f"{name}{h.VIEW_SUFFIX}"
        if not bp.exists():
            yield "skip", name, f"no blueprint at {bp}"
            continue
        try:
            repo_obj = h.normalize_metric_view(yaml.safe_load(bp.read_text()), cfg)
            live_obj = h.normalize_metric_view(
                h.export_metric_view(adapter, name, cfg), cfg)
            rt, lt = h.canonical_json(repo_obj), h.canonical_json(live_obj)
            if rt != lt:
                yield "drift", name, unified_diff(rt, lt, f"{name}{h.VIEW_SUFFIX}")
            else:
                yield "ok", name, ""
        except (ConfigError, PermanentError, TransientError, DriftDefenseError) as e:
            yield "error", name, str(e)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="L2 nightly drift audit")
    ap.add_argument("--env", default="prod")
    ap.add_argument("--open-workitem", action="store_true")
    args = ap.parse_args(argv)

    cfg = h.load_config()
    adapter = h.DatabricksAdapter(cfg["workspace"]["host"])

    drifts, errors = [], []
    log.info("L2 drift audit — env=%s", args.env)

    log.info("Genie spaces:")
    for status, name, detail in audit_spaces(cfg, args.env, adapter):
        _emit(status, "space", name, detail, drifts, errors)
    log.info("Metric views:")
    for status, name, detail in audit_metric_views(cfg, adapter):
        _emit(status, "metric view", name, detail, drifts, errors)

    if drifts:
        print("\n" + "=" * 70)
        log.error("L2 FOUND DRIFT in %d object(s).", len(drifts))
        for kind, name, diff in drifts:
            print(f"\n--- {kind}: {name} ---\n{diff or '(differs; inspect manually)'}")
            if args.open_workitem:
                open_azure_workitem(
                    f"[Genie drift] {kind} '{name}' diverged from repo ({args.env})",
                    f"Nightly L2 audit found the live object differs from the repo "
                    f"blueprint (likely a UI edit). Resolve by redeploying the "
                    f"blueprint OR committing the intended change via PR.\n\n{diff}")
        print("\nRemediation is a human decision. Do not auto-revert.")
        return 3

    if errors:
        log.error("L2 had no drift but %d object(s) errored — investigate.", len(errors))
        return 7

    log.info("L2 PASSED — live workspace matches the repo for all managed objects.")
    return 0


def _emit(status, kind, name, detail, drifts, errors):
    if status == "ok":
        log.info("  ok:    %s '%s'", kind, name)
    elif status == "drift":
        log.error("  DRIFT: %s '%s'", kind, name)
        drifts.append((kind, name, detail))
    elif status == "error":
        log.error("  ERROR: %s '%s' — %s", kind, name, detail)
        errors.append((kind, name, detail))
    else:  # skip
        log.warning("  skip:  %s '%s' — %s", kind, name, detail)


def _entry() -> int:
    try:
        return main()
    except ConfigError as e:
        log.error("setup/config error: %s", e)
        return 2
    except Exception as e:
        log.error("unexpected error: %s", e)
        return 2


if __name__ == "__main__":
    sys.exit(_entry())
