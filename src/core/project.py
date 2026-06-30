from dataclasses import dataclass
from pathlib import Path

_MARKERS = ["go.mod", "pyproject.toml", "package.json", "Cargo.toml", ".git"]


@dataclass
class ProjectPaths:
    root: Path
    specify_dir: Path
    db_path: Path
    index_md: Path
    tasks_dir: Path


def find_project_root(start: Path | None = None) -> Path | None:
    start = start or Path.cwd()
    for parent in [start, *start.parents]:
        if any((parent / m).exists() for m in _MARKERS):
            return parent
    return None


def get_project_paths(start: Path | None = None) -> ProjectPaths:
    root = find_project_root(start)
    if root is None:
        raise RuntimeError(
            "Raiz do projeto não encontrada. Execute dentro de um repositório."
        )
    specify_dir = root / ".specify"
    return ProjectPaths(
        root=root,
        specify_dir=specify_dir,
        db_path=specify_dir / "specify.db",
        index_md=specify_dir / "INDEX.md",
        tasks_dir=specify_dir / "tasks",
    )
