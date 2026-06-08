"""Tests for L1 find_violations and L2b grading/determinism logic."""
from __future__ import annotations

import pytest

import check_colocation as l1
import run_benchmarks as l2b


# ============================== L1 ==============================
def test_l1_model_alone_blocks(valid_config):
    v = l1.find_violations(valid_config, {"models/rates_fact.sql"}, set())
    assert len(v) == 1 and "nim" in v[0]


def test_l1_model_plus_view_blocks_space(valid_config):
    # nim depends on rates_fact; treasury depends on nim. Changing model+view
    # but not the space must flag the space.
    changed = {"models/rates_fact.sql", "metric_views/nim.metricview.yaml"}
    v = l1.find_violations(valid_config, changed, set())
    assert len(v) == 1 and "treasury" in v[0]


def test_l1_all_three_together_passes(valid_config):
    changed = {"models/rates_fact.sql", "metric_views/nim.metricview.yaml",
               "genie_spaces/treasury.genie.json"}
    assert l1.find_violations(valid_config, changed, set()) == []


def test_l1_ack_clears_view_violation(valid_config):
    v = l1.find_violations(valid_config, {"models/rates_fact.sql"}, {"nim"})
    assert v == []


def test_l1_unrelated_file_passes(valid_config):
    assert l1.find_violations(valid_config, {"README.md"}, set()) == []


def test_l1_parse_acks():
    txt = "Some PR body.\ndrift-ack: nim no impact\ndrift-ack: treasury reviewed"
    assert l1.parse_acks(txt) == {"nim", "treasury"}


def test_l1_unrelated_model_change_does_not_flag_other_view(valid_config):
    # deposits_fact feeds 'deposits', not 'nim'. Changing it must not flag nim.
    v = l1.find_violations(valid_config, {"models/deposits_fact.sql"}, set())
    assert len(v) == 1 and "deposits" in v[0] and "nim" not in v[0]


# ============================== L2b grading ==============================
def test_grade_scalar_within_tol():
    ok, _ = l2b.grade_scalar(1000, [[1003]], 0.005)
    assert ok


def test_grade_scalar_over_tol():
    ok, _ = l2b.grade_scalar(1000, [[1006]], 0.005)
    assert not ok


def test_grade_scalar_zero_golden():
    assert l2b.grade_scalar(0, [[0]], 0.005)[0]
    assert not l2b.grade_scalar(0, [[5]], 0.005)[0]


def test_grade_scalar_non_numeric():
    assert not l2b.grade_scalar(1000, [["x"]], 0.005)[0]
    assert not l2b.grade_scalar(1000, [], 0.005)[0]


def test_grade_rowset_order_insensitive():
    g = [["Rates", 100], ["FX", 50]]
    assert l2b.grade_rowset(g, [["FX", 50], ["Rates", 100]])[0]


def test_grade_rowset_detects_diff():
    g = [["Rates", 100]]
    assert not l2b.grade_rowset(g, [["Rates", 101]])[0]
    assert not l2b.grade_rowset(g, [])[0]


def test_grade_sql_fragment_present():
    assert l2b.grade_sql("finance.analytics.nim",
                         "SELECT MEASURE(nim) FROM finance.analytics.nim LIMIT 100")[0]


def test_grade_sql_fragment_absent():
    assert not l2b.grade_sql("finance.analytics.nim",
                             "SELECT * FROM raw.deposits")[0]


def test_grade_sql_no_sql():
    assert not l2b.grade_sql("finance.analytics.nim", None)[0]


@pytest.mark.parametrize("text,flag", [
    ("total as of CURRENT_DATE", True),
    ("select now()", True),
    ("GETDATE()", True),
    ("current_timestamp", True),
    ("As of 2026-01-31, total deposits", False),
    ("measure(nim)", False),
])
def test_determinism_guard(text, flag):
    assert l2b.is_nondeterministic(text) is flag
