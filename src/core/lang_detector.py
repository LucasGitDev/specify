from dataclasses import dataclass
from pathlib import Path


@dataclass
class LangConfig:
    language: str
    test_cmd: str
    lint_cmd: str
    fmt_cmd: str


_CONFIGS: list[tuple[str, LangConfig]] = [
    ("go.mod",         LangConfig("go",         "go test ./...",  "go vet ./...",          "gofmt -l .")),
    ("pyproject.toml", LangConfig("python",      "pytest",         "ruff check .",          "ruff format --check .")),
    ("package.json",   LangConfig("typescript",  "npm test",       "npm run lint",          "prettier --check .")),
    ("Cargo.toml",     LangConfig("rust",        "cargo test",     "cargo clippy",          "cargo fmt --check")),
]


def detect(root: Path) -> LangConfig | None:
    for marker, config in _CONFIGS:
        if (root / marker).exists():
            return config
    return None
