"""Tests for DatabricksAdapter against the fake SDK client."""
from __future__ import annotations

import json

import pytest

import databricks_helpers as h
from _core import PermanentError
from conftest import (FakeGenie, FakeStatementExecution, FakeWorkspaceClient,
                      _Obj)


def make_adapter(genie=None, se=None):
    client = FakeWorkspaceClient(genie=genie, statement_execution=se)
    return h.DatabricksAdapter(client=client)


def test_export_space_parses_serialized_and_etag():
    ser = json.dumps({"title": "T", "instructions": {"text_instructions": "hi"}})
    genie = FakeGenie(spaces={"d1": {"serialized_space": ser, "etag": "E1"}})
    adapter = make_adapter(genie)
    parsed, etag = adapter.export_space("d1")
    assert parsed["title"] == "T"
    assert etag == "E1"


def test_export_space_missing_serialized_raises():
    # space exists but no serialized_space (e.g. CAN EDIT not granted)
    genie = FakeGenie(spaces={"d1": {"etag": "E1"}})
    adapter = make_adapter(genie)
    with pytest.raises(PermanentError, match="no serialized_space"):
        adapter.export_space("d1")


def test_update_space_passes_etag():
    genie = FakeGenie(spaces={"p1": {"serialized_space": "{}", "etag": "E1"}})
    adapter = make_adapter(genie)
    adapter.update_space("p1", serialized_space="{}", warehouse_id="wh1", etag="E1")
    assert genie.updated == [("p1", "{}", "E1")]


def test_update_space_etag_conflict_is_permanent():
    genie = FakeGenie(spaces={"p1": {"serialized_space": "{}"}},
                      fail_update_with=RuntimeError("etag mismatch: 409"))
    adapter = make_adapter(genie)
    with pytest.raises(PermanentError):
        adapter.update_space("p1", serialized_space="{}", warehouse_id="wh1",
                             etag="STALE")


def test_run_sql_returns_rows():
    se = FakeStatementExecution(rows=[["123"]], state="SUCCEEDED")
    adapter = make_adapter(se=se)
    rows = adapter.run_sql("wh1", "DESCRIBE TABLE EXTENDED finance.analytics.nim AS JSON")
    assert rows == [["123"]]


def test_run_sql_failed_state_is_permanent():
    se = FakeStatementExecution(rows=[], state="FAILED")
    adapter = make_adapter(se=se)
    with pytest.raises(PermanentError, match="did not succeed"):
        adapter.run_sql("wh1", "SELECT bad")


def test_ask_extracts_sql_and_rows():
    genie = FakeGenie(ask_result=("SELECT measure(nim) FROM finance.analytics.nim",
                                  [[4823000000]]))
    adapter = make_adapter(genie)
    sql, rows = adapter.ask("p1", "nim as of 2026-01-31")
    assert "finance.analytics.nim" in sql
    assert rows == [[4823000000]]


def test_ask_no_attachment_returns_empty():
    genie = FakeGenie(ask_result=(None, []))
    adapter = make_adapter(genie)
    sql, rows = adapter.ask("p1", "something")
    assert sql is None and rows == []


def test_export_metric_view_parses_describe_json(valid_config):
    payload = json.dumps({"name": "nim", "measures": [{"name": "nim", "expr": "x"}]})
    se = FakeStatementExecution(rows=[[payload]], state="SUCCEEDED")
    adapter = make_adapter(se=se)
    out = h.export_metric_view(adapter, "nim", valid_config)
    assert out["name"] == "nim"


def test_export_metric_view_rejects_bad_identifier(valid_config):
    se = FakeStatementExecution(rows=[["{}"]], state="SUCCEEDED")
    adapter = make_adapter(se=se)
    with pytest.raises(Exception):
        h.export_metric_view(adapter, "nim; DROP TABLE x", valid_config)
