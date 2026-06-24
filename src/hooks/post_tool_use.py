#!/usr/bin/env python3
"""PostToolUse hook — loga tool calls em specify.log quando SPECIFY_DEBUG=1."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

if not os.environ.get("SPECIFY_DEBUG"):
    sys.exit(0)

log_path = Path(
    os.environ.get("SPECIFY_LOG_PATH", Path.home() / ".claude" / "specify.log")
)

try:
    data = json.load(sys.stdin)
    tool_name = data.get("tool_name", "?")
    tool_input = data.get("tool_input", {})
    input_preview = repr(str(tool_input))[:300]
    response = data.get("tool_response", {})
    is_error = response.get("is_error", False)
    status = "error" if is_error else "ok"

    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    line = f"[{ts}] [DEBUG] post_tool_use: {tool_name} status={status} input={input_preview}\n"

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line)
except Exception:
    pass
