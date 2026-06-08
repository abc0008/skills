"""Tests for config validation, normalization, identifier safety, helpers."""
from __future__ import annotations

import copy
import json

import pytest

import databricks_helpers as h
from _core import ConfigError


# ---- config validation -------------------------------------------------------
def test_valid_config_passes(valid_config):
    h.validate_config(valid_config)  # should not raise


def test_missing_workspace_key(valid_config):
    cfg = copy.deepcopy(valid_config)
    del cfg["workspace"]["warehouse_id"]
    with pytest.raises(ConfigError, match="missing required keys"):
        h.validate_config(cfg)


def test_placeholder_values_rejected(valid_config):
    cfg = copy.deepcopy(valid_config)
    cfg["workspace"]["warehouse_id"] = "REPLACE_WITH_SQL_WAREHOUSE_ID"
    with pytest.raises(ConfigError, match="placeholder"):
        h.validate_config(cfg)


def test_dangling_metric_view_reference(valid_config):
    cfg = copy.deepcopy(valid_config)
    cfg["genie_spaces"]["treasury"]["depends_on_metric_views"] = ["does_not_exist"]
    with pytest.raises(ConfigError, match="not defined under metric_views"):
        h.validate_config(cfg)


def test_space_id_by_env_must_be_mapping(valid_config):
    cfg = copy.deepcopy(valid_config)
    cfg["genie_spaces"]["treasury"]["space_id_by_env"] = "p1"
    with pytest.raises(ConfigError, match="must be a mapping"):
        h.validate_config(cfg)


def test_get_space_id(valid_config):
    assert h.get_space_id(valid_config, "treasury", "prod") == "p1"
    with pytest.raises(ConfigError):
        h.get_space_id(valid_config, "treasury", "staging")
    with pytest.raises(ConfigError):
        h.get_space_id(valid_config, "nope", "prod")


# ---- logical_name ------------------------------------------------------------
@pytest.mark.parametrize("path,expected", [
    ("metric_views/nim.metricview.yaml", "nim"),
    ("genie_spaces/treasury.genie.json", "treasury"),
    ("benchmarks/treasury.bench.yaml", "treasury"),
    ("models/instrument_dim.sql", "instrument_dim"),
])
def test_logical_name(path, expected):
    assert h.logical_name(path) == expected


# ---- normalization -----------------------------------------------------------
def test_normalize_space_strips_env_fields(valid_config):
    space = {"space_id": "x", "etag": "abc", "title": "T",
             "data_sources": [{"identifier": "t", "warehouse_id": "wh"}]}
    out = h.normalize_space(space, valid_config)
    assert "space_id" not in out and "etag" not in out
    assert out["title"] == "T"
    # nested strip
    assert "warehouse_id" not in out["data_sources"][0]


def test_canonical_json_is_order_independent():
    a = {"b": 1, "a": 2}
    b = {"a": 2, "b": 1}
    assert h.canonical_json(a) == h.canonical_json(b)


# ---- identifier safety (SQL injection guard) --------------------------------
@pytest.mark.parametrize("bad", ["a;drop table x", "a.b", "1abc", "a-b", "", "a b"])
def test_unsafe_identifier_rejected(bad):
    with pytest.raises(ConfigError):
        h._assert_safe_identifier(bad)


@pytest.mark.parametrize("good", ["nim", "deposits_v2", "_x", "Finance"])
def test_safe_identifier_allowed(good):
    h._assert_safe_identifier(good)  # no raise
