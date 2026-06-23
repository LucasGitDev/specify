from pathlib import Path

import pytest

from src.core.gate_validator import GateResult, run_gate
from src.core.spec_reader import extract_criteria, validate

FIXTURES = Path(__file__).parent.parent / "fixtures"


# --- gate_validator ---

def test_run_gate_success(tmp_path):
    result = run_gate("echo ok", tmp_path)
    assert result.passed is True
    assert "ok" in result.output
    assert result.duration_ms >= 0
    assert result.command == "echo ok"


def test_run_gate_failure(tmp_path):
    # 'false' é comando POSIX que retorna exit code 1
    result = run_gate("false", tmp_path)
    assert result.passed is False


def test_run_gate_command_not_found(tmp_path):
    result = run_gate("comando-inexistente-xyz", tmp_path)
    assert result.passed is False
    assert "não encontrado" in result.output


def test_run_gate_timeout(tmp_path):
    result = run_gate("sleep 10", tmp_path, timeout=1)
    assert result.passed is False
    assert "timeout" in result.output


def test_run_gate_captures_stderr(tmp_path):
    # redirecionar stderr via shell não funciona sem shell=True;
    # usar python para emitir em stderr
    result = run_gate("python3 -c \"import sys; sys.stderr.write('err')\"", tmp_path)
    assert "err" in result.output


def test_run_gate_gate_type_preserved(tmp_path):
    result = run_gate("echo x", tmp_path, gate_type="lint")
    assert result.gate_type == "lint"


# --- spec_reader.validate ---

def test_validate_valid_spec():
    content = "# Minha Feature\n\n## Critérios de Sucesso\n\n- item 1\n- item 2\n"
    v = validate(content)
    assert v.valid is True
    assert v.title == "Minha Feature"
    assert v.errors == []


def test_validate_empty_spec():
    v = validate("")
    assert v.valid is False
    assert len(v.errors) > 0


def test_validate_missing_title():
    content = "## Critérios\n\n- item\n"
    v = validate(content)
    assert v.valid is False
    assert any("título" in e for e in v.errors)


def test_validate_missing_criteria():
    content = "# Título\n\nSem seção de critérios aqui.\n"
    v = validate(content)
    assert v.valid is False
    assert any("critério" in e.lower() for e in v.errors)


def test_validate_english_success_heading():
    content = "# Feature\n\n## Acceptance Criteria\n\n- item\n"
    v = validate(content)
    assert v.valid is True


# --- spec_reader.extract_criteria ---

def test_extract_criteria_basic():
    content = "# Título\n\n## Critérios de Sucesso\n\n- Item A\n- Item B\n"
    items = extract_criteria(content)
    assert items == ["Item A", "Item B"]


def test_extract_criteria_stops_at_next_section():
    content = "# Título\n\n## Critérios\n\n- A\n- B\n\n## Outra Seção\n\n- C\n"
    items = extract_criteria(content)
    assert items == ["A", "B"]
    assert "C" not in items


def test_extract_criteria_empty_when_no_section():
    content = "# Título\n\nSem critérios aqui.\n"
    assert extract_criteria(content) == []
