"""Tests for studio bugs: layout isolation and filter UI survival."""

from __future__ import annotations

import re
from pathlib import Path

INDEX_HTML = Path("src/studio/static/index.html")


def _html() -> str:
    return INDEX_HTML.read_text()


# ── Bug 2: filter buttons disappear on toggle ────────────────────────────────


def test_sigma_container_div_exists():
    """Sigma must render into a dedicated sub-container, not graph-container.
    Sigma.kill() clears its container's innerHTML; if toolbar lives there it disappears."""
    assert 'id="sigma-container"' in _html(), (
        "sigma-container div must exist as a dedicated Sigma render target"
    )


def test_toolbar_appears_before_sigma_container():
    """toolbar must be a sibling of sigma-container (or precede it), never a child."""
    content = _html()
    sigma_idx = content.find('id="sigma-container"')
    toolbar_idx = content.find('id="toolbar"')
    assert sigma_idx != -1, "sigma-container must exist"
    assert toolbar_idx != -1, "toolbar must exist"
    assert toolbar_idx < sigma_idx, (
        "toolbar must appear before sigma-container in HTML (sibling, not child)"
    )


def test_sigma_initialized_with_sigma_container():
    """new Sigma(...) must receive sigmaContainer, not the full graph-container."""
    content = _html()
    assert re.search(r"new Sigma\s*\(\s*\w+\s*,\s*sigmaContainer", content), (
        "Sigma must be initialized with sigmaContainer variable"
    )


def test_rebuild_graph_references_sigma_container():
    """rebuildGraph must pass sigmaContainer to Sigma to avoid clobbering toolbar."""
    content = _html()
    # Locate rebuildGraph function body
    m = re.search(
        r"async function rebuildGraph\(\)(.*?)(?=\nasync function|\nfunction )",
        content,
        re.DOTALL,
    )
    assert m, "rebuildGraph function must exist"
    assert "sigmaContainer" in m.group(1), (
        "rebuildGraph must use sigmaContainer when creating Sigma instance"
    )


# ── Bug 1: task nodes appear far from connected memories ─────────────────────


def test_layout_reads_edge_kind_attribute():
    """applyLayout must read edge kind to apply differential attraction forces."""
    content = _html()
    layout_match = re.search(
        r"function applyLayout\((.*?)(?=\nfunction )", content, re.DOTALL
    )
    assert layout_match, "applyLayout function must exist"
    body = layout_match.group(1)
    assert "kind" in body, (
        "applyLayout must read edge kind attribute to differentiate force"
    )


def test_layout_uses_stronger_force_for_scope_edges():
    """scope-link edges must attract with a stronger force than semantic edges."""
    content = _html()
    layout_match = re.search(
        r"function applyLayout\((.*?)(?=\nfunction )", content, re.DOTALL
    )
    assert layout_match, "applyLayout must exist"
    body = layout_match.group(1)
    # Must have a scope-specific force (e.g. different divisor for scope edges)
    has_scope_branch = bool(
        re.search(r"scope", body) and re.search(r"scope.*\d|\d.*scope", body)
    )
    assert has_scope_branch, (
        "applyLayout must apply a stronger (scope-specific) attraction force for scope edges"
    )


def test_init_graph_uses_sigma_container():
    """initGraph must also use sigmaContainer so initial load is consistent with rebuild."""
    content = _html()
    m = re.search(
        r"async function initGraph\(\)(.*?)(?=\nasync function|\nfunction )",
        content,
        re.DOTALL,
    )
    assert m, "initGraph function must exist"
    assert "sigmaContainer" in m.group(1), (
        "initGraph must use sigmaContainer (same as rebuildGraph)"
    )
