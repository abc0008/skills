"""Integration test: L2 audit detects drift between repo blueprint and live."""
from __future__ import annotations

import json

import databricks_helpers as h
import audit_drift as l2
from conftest import FakeGenie, FakeWorkspaceClient


def _write_blueprint(tmp_path, monkeypatch, name, obj):
    spaces_dir = tmp_path / "genie_spaces"
    spaces_dir.mkdir(exist_ok=True)
    (spaces_dir / f"{name}{h.SPACE_SUFFIX}").write_text(h.canonical_json(obj) + "\n")
    monkeypatch.setattr(h, "GENIE_SPACES_DIR", spaces_dir)


def test_audit_detects_match(tmp_path, monkeypatch, valid_config):
    # Repo blueprint and live are identical after normalization.
    blueprint = {"title": "Treasury", "instructions": {"text_instructions": "use nim"}}
    _write_blueprint(tmp_path, monkeypatch, "treasury", blueprint)
    # live carries extra env fields that normalize() strips -> still matches
    live = dict(blueprint, space_id="p1", etag="E1", warehouse_id="wh1")
    genie = FakeGenie(spaces={"p1": {"serialized_space": json.dumps(live), "etag": "E1"}})
    adapter = h.DatabricksAdapter(client=FakeWorkspaceClient(genie=genie))

    cfg = dict(valid_config)
    cfg["genie_spaces"] = {"treasury": valid_config["genie_spaces"]["treasury"]}
    results = list(l2.audit_spaces(cfg, "prod", adapter))
    assert results == [("ok", "treasury", "")]


def test_audit_detects_drift(tmp_path, monkeypatch, valid_config):
    blueprint = {"title": "Treasury", "instructions": {"text_instructions": "use nim"}}
    _write_blueprint(tmp_path, monkeypatch, "treasury", blueprint)
    # live has a DIFFERENT instruction -> drift
    live = {"title": "Treasury", "instructions": {"text_instructions": "use RAW table"},
            "space_id": "p1", "etag": "E2"}
    genie = FakeGenie(spaces={"p1": {"serialized_space": json.dumps(live), "etag": "E2"}})
    adapter = h.DatabricksAdapter(client=FakeWorkspaceClient(genie=genie))

    cfg = dict(valid_config)
    cfg["genie_spaces"] = {"treasury": valid_config["genie_spaces"]["treasury"]}
    results = list(l2.audit_spaces(cfg, "prod", adapter))
    status, name, detail = results[0]
    assert status == "drift" and name == "treasury"
    assert "use RAW table" in detail  # the diff shows the live (wrong) value


def test_audit_handles_missing_blueprint(tmp_path, monkeypatch, valid_config):
    spaces_dir = tmp_path / "genie_spaces"
    spaces_dir.mkdir()
    monkeypatch.setattr(h, "GENIE_SPACES_DIR", spaces_dir)
    genie = FakeGenie(spaces={})
    adapter = h.DatabricksAdapter(client=FakeWorkspaceClient(genie=genie))
    cfg = dict(valid_config)
    cfg["genie_spaces"] = {"treasury": valid_config["genie_spaces"]["treasury"]}
    results = list(l2.audit_spaces(cfg, "prod", adapter))
    assert results[0][0] == "skip"
