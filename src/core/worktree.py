from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WorktreeInfo:
    path: Path
    branch: str
    commit: str
    is_main: bool


def _run_git(project_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project_root), *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} falhou: {result.stderr.strip()}")
    return result.stdout.strip()


def _worktrees_base(project_root: Path) -> Path:
    return project_root / ".claude" / "worktrees"


def _worktree_path(project_root: Path, name: str) -> Path:
    return _worktrees_base(project_root) / name


def _branch_name(name: str) -> str:
    return f"specify/{name}"


def list_worktrees(project_root: Path) -> list[WorktreeInfo]:
    output = _run_git(project_root, "worktree", "list", "--porcelain")
    worktrees: list[WorktreeInfo] = []
    current: dict = {}
    for line in output.splitlines():
        if line.startswith("worktree "):
            if current:
                worktrees.append(_parse_worktree(current))
            current = {"path": line[len("worktree ") :]}
        elif line.startswith("HEAD "):
            current["commit"] = line[len("HEAD ") :]
        elif line.startswith("branch "):
            current["branch"] = line[len("branch refs/heads/") :]
        elif line == "bare":
            current["branch"] = "(bare)"
    if current:
        worktrees.append(_parse_worktree(current))
    return worktrees


def _parse_worktree(data: dict) -> WorktreeInfo:
    path = Path(data.get("path", ""))
    branch = data.get("branch", "(detached)")
    commit = data.get("commit", "")
    # primeiro worktree listado é sempre o principal
    return WorktreeInfo(path=path, branch=branch, commit=commit, is_main=False)


def _default_branch(project_root: Path) -> str:
    """Detecta branch padrão do repositório (main ou master)."""
    for candidate in ("main", "master"):
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "--verify", candidate],
            capture_output=True,
        )
        if result.returncode == 0:
            return candidate
    # fallback: HEAD atual
    return _run_git(project_root, "rev-parse", "--abbrev-ref", "HEAD")


def create(
    project_root: Path,
    name: str,
    base_branch: str | None = None,
) -> WorktreeInfo:
    wt_path = _worktree_path(project_root, name)
    branch = _branch_name(name)

    if wt_path.exists():
        raise RuntimeError(
            f"worktree já existe em '{wt_path}'. "
            "Use worktree.remove() antes de recriar."
        )

    if base_branch is None:
        base_branch = _default_branch(project_root)

    wt_path.parent.mkdir(parents=True, exist_ok=True)
    _run_git(project_root, "worktree", "add", str(wt_path), "-b", branch, base_branch)

    commit = _run_git(project_root, "rev-parse", "HEAD")
    return WorktreeInfo(path=wt_path, branch=branch, commit=commit, is_main=False)


def remove(
    project_root: Path,
    worktree_path: Path,
    force: bool = False,
) -> None:
    args = ["worktree", "remove", str(worktree_path)]
    if force:
        args.append("--force")
    _run_git(project_root, *args)

    # remover branch local se ainda existir
    branch = _run_git_safe(
        project_root, "rev-parse", "--abbrev-ref", f"specify/{worktree_path.name}"
    )
    if branch:
        _run_git_safe(project_root, "branch", "-D", f"specify/{worktree_path.name}")


def _run_git_safe(project_root: Path, *args: str) -> str:
    """Como _run_git mas retorna '' em caso de erro (não levanta)."""
    result = subprocess.run(
        ["git", "-C", str(project_root), *args],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def exists(project_root: Path, name: str) -> bool:
    return _worktree_path(project_root, name).exists()


def get_info(project_root: Path, name: str) -> WorktreeInfo | None:
    wt_path = _worktree_path(project_root, name)
    if not wt_path.exists():
        return None
    commit = _run_git_safe(
        project_root, "rev-parse", f"specify/{name}"
    ) or _run_git_safe(project_root, "rev-parse", "HEAD")
    return WorktreeInfo(
        path=wt_path,
        branch=_branch_name(name),
        commit=commit,
        is_main=False,
    )
