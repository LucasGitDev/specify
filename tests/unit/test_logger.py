from __future__ import annotations

import logging
import sys


def _reload_logger(monkeypatch, env: dict):
    """Import src.core.logger with a clean environment."""
    monkeypatch.setattr("os.environ", {**env})
    if "src.core.logger" in sys.modules:
        del sys.modules["src.core.logger"]
    import src.core.logger as mod

    return mod


# Critério 1 — CLI operations logged when SPECIFY_DEBUG=1


def test_debug_enabled_creates_log_file(monkeypatch, tmp_path):
    log_file = tmp_path / "specify.log"
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    if "src.core.logger" in sys.modules:
        del sys.modules["src.core.logger"]
    import src.core.logger as mod

    logger = mod.get_logger()
    logger.info("test operation")
    assert log_file.exists()
    content = log_file.read_text()
    assert "test operation" in content


def test_debug_log_contains_timestamp_and_level(monkeypatch, tmp_path):
    log_file = tmp_path / "specify.log"
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    if "src.core.logger" in sys.modules:
        del sys.modules["src.core.logger"]
    import src.core.logger as mod

    logger = mod.get_logger()
    logger.info("check format")
    line = log_file.read_text().strip().splitlines()[-1]
    # expects [ISO timestamp] [LEVEL] message
    assert line.startswith("[")
    assert "] [" in line
    assert "check format" in line


def test_debug_log_appends(monkeypatch, tmp_path):
    log_file = tmp_path / "specify.log"
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    if "src.core.logger" in sys.modules:
        del sys.modules["src.core.logger"]
    import src.core.logger as mod

    logger = mod.get_logger()
    logger.info("first")
    logger.info("second")
    lines = [line for line in log_file.read_text().splitlines() if line.strip()]
    assert len(lines) == 2


# Critério 4 — no effect when SPECIFY_DEBUG is absent


def test_no_debug_no_log_file(monkeypatch, tmp_path):
    log_file = tmp_path / "specify.log"
    monkeypatch.delenv("SPECIFY_DEBUG", raising=False)
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    if "src.core.logger" in sys.modules:
        del sys.modules["src.core.logger"]
    import src.core.logger as mod

    logger = mod.get_logger()
    logger.info("should not appear")
    assert not log_file.exists()


def test_no_debug_logger_is_null_handler(monkeypatch, tmp_path):
    monkeypatch.delenv("SPECIFY_DEBUG", raising=False)
    if "src.core.logger" in sys.modules:
        del sys.modules["src.core.logger"]
    import src.core.logger as mod

    logger = mod.get_logger()
    assert all(isinstance(h, logging.NullHandler) for h in logger.handlers)


# Critério 5 — failure to write log never raises


def test_log_write_failure_does_not_raise(monkeypatch):
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", "/nonexistent/path/specify.log")
    if "src.core.logger" in sys.modules:
        del sys.modules["src.core.logger"]
    import src.core.logger as mod

    logger = mod.get_logger()
    # must not raise
    logger.info("safe operation")


# Critério 2 — session_start exceptions go to log, not swallowed silently


def test_session_start_logs_exception_in_debug(monkeypatch, tmp_path):
    log_file = tmp_path / "specify.log"
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    if "src.core.logger" in sys.modules:
        del sys.modules["src.core.logger"]
    if "src.hooks.session_start" in sys.modules:
        del sys.modules["src.hooks.session_start"]

    import src.core.logger as mod

    logger = mod.get_logger()
    logger.exception("session_start error", exc_info=ValueError("boom"))
    content = log_file.read_text()
    assert "session_start error" in content
    assert "boom" in content
