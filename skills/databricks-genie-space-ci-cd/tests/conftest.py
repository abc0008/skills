"""
conftest.py — shared pytest fixtures and a fake Databricks client so the entire
suite runs with NO live workspace and NO databricks-sdk installed.

The fake mimics just enough of the SDK surface our adapter touches:
  client.genie.get_space / create_space / update_space /
        start_conversation_and_wait / get_message_attachment_query_result
  client.statement_execution.execute_statement

Tests inject it via DatabricksAdapter(client=FakeWorkspaceClient(...)).
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

# Make ci/ importable as top-level modules (_core, databricks_helpers, ...).
CI_DIR = Path(__file__).resolve().parents[1] / "ci"
sys.path.insert(0, str(CI_DIR))


# ------------------------------------------------------------------------------
# Fake SDK objects
# ------------------------------------------------------------------------------
class _Obj:
    """Generic attribute bag that also supports as_dict()."""
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def as_dict(self):
        return dict(self.__dict__)


class FakeGenie:
    def __init__(self, spaces=None, ask_result=None, fail_update_with=None):
        # spaces: {space_id: {"serialized_space": <json str>, "etag": "..."}}
        self._spaces = spaces or {}
        self._ask_result = ask_result  # (generated_sql, rows)
        self._fail_update_with = fail_update_with
        self.updated = []
        self.created = []

    def get_space(self, space_id, include_serialized_space=False):
        if space_id not in self._spaces:
            raise RuntimeError("not found: 404")
        d = dict(self._spaces[space_id])
        if not include_serialized_space:
            d.pop("serialized_space", None)
        return _Obj(**d)

    def create_space(self, warehouse_id, serialized_space, title=None,
                     parent_path=None, description=None):
        new_id = f"new-{len(self.created)}"
        self.created.append((new_id, serialized_space))
        return _Obj(space_id=new_id)

    def update_space(self, space_id, serialized_space=None, warehouse_id=None,
                     etag=None, **kw):
        if self._fail_update_with:
            raise self._fail_update_with
        self.updated.append((space_id, serialized_space, etag))
        return _Obj(space_id=space_id)

    def start_conversation_and_wait(self, space_id, content):
        sql, rows = self._ask_result or (None, [])
        if sql is None:
            return _Obj(conversation_id="c1", id="m1", attachments=[])
        att = _Obj(attachment_id="a1", query=_Obj(query=sql))
        return _Obj(conversation_id="c1", id="m1", attachments=[att])

    def get_message_attachment_query_result(self, space_id, conversation_id,
                                            message_id, attachment_id):
        _sql, rows = self._ask_result or (None, [])
        return _Obj(statement_response=_Obj(result=_Obj(data_array=rows)))


class FakeStatementExecution:
    def __init__(self, rows=None, state="SUCCEEDED"):
        self._rows = rows or []
        self._state = state

    def execute_statement(self, warehouse_id, statement, wait_timeout="50s"):
        return _Obj(status=_Obj(state=self._state),
                    result=_Obj(data_array=self._rows))


class FakeWorkspaceClient:
    def __init__(self, genie=None, statement_execution=None):
        self.genie = genie or FakeGenie()
        self.statement_execution = statement_execution or FakeStatementExecution()


# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------
@pytest.fixture
def valid_config():
    return {
        "workspace": {"host": "https://w.example.com", "warehouse_id": "wh1",
                      "catalog": "finance", "schema": "analytics"},
        "metric_views": {
            "nim": {"depends_on_models": ["models/instrument_dim.sql",
                                          "models/rates_fact.sql"]},
            "deposits": {"depends_on_models": ["models/deposits_fact.sql"]},
        },
        "genie_spaces": {
            "treasury": {"space_id_by_env": {"dev": "d1", "prod": "p1"},
                         "depends_on_metric_views": ["nim"],
                         "depends_on_models": []},
            "retail_deposits": {"space_id_by_env": {"dev": "d2", "prod": "p2"},
                                "depends_on_metric_views": ["deposits"],
                                "depends_on_models": []},
        },
        "normalize": {"strip_space_fields": ["space_id", "etag", "created_at",
                                             "warehouse_id"],
                      "strip_view_fields": ["owner", "created_at"]},
    }


@pytest.fixture
def fake_client():
    return FakeWorkspaceClient()
