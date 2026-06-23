from dataclasses import dataclass
from pathlib import Path


@dataclass
class LangConfig:
    language: str
    test_cmd: str
    lint_cmd: str
    fmt_cmd: str


_GO = LangConfig(
    language="go",
    test_cmd="go test ./...",
    lint_cmd="go vet ./...",
    fmt_cmd="gofmt -l .",
)


def detect(root: Path) -> LangConfig | None:
    if (root / "go.mod").exists():
        return _GO
    return None
