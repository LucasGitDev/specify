from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from src.core.worktree import (
    WorktreeInfo,
    create,
    exists,
    get_info,
    list_worktrees,
    remove,
)


@pytest.fixture
def git_repo(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@test.com"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Test"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "--allow-empty", "-m", "init"],
        check=True, capture_output=True,
    )
    return tmp_path


def test_create_creates_directory(git_repo):
    info = create(git_repo, "feat-x")
    expected = git_repo / ".claude" / "worktrees" / "feat-x"
    assert expected.exists()
    assert info.path == expected


def test_create_uses_specify_branch(git_repo):
    info = create(git_repo, "feat-x")
    assert info.branch == "specify/feat-x"


def test_exists_true_after_create(git_repo):
    create(git_repo, "feat-x")
    assert exists(git_repo, "feat-x") is True


def test_exists_false_before_create(git_repo):
    assert exists(git_repo, "nao-existe") is False


def test_get_info_returns_worktreeinfo(git_repo):
    create(git_repo, "feat-x")
    info = get_info(git_repo, "feat-x")
    assert info is not None
    assert isinstance(info, WorktreeInfo)
    assert info.branch == "specify/feat-x"


def test_get_info_returns_none_for_missing(git_repo):
    assert get_info(git_repo, "nao-existe") is None


def test_list_includes_created_worktree(git_repo):
    create(git_repo, "feat-x")
    wts = list_worktrees(git_repo)
    paths = [w.path for w in wts]
    expected = git_repo / ".claude" / "worktrees" / "feat-x"
    assert expected in paths


def test_remove_deletes_directory(git_repo):
    info = create(git_repo, "feat-x")
    remove(git_repo, info.path)
    assert not info.path.exists()


def test_exists_false_after_remove(git_repo):
    info = create(git_repo, "feat-x")
    remove(git_repo, info.path)
    assert exists(git_repo, "feat-x") is False


def test_create_raises_if_already_exists(git_repo):
    create(git_repo, "feat-x")
    with pytest.raises(RuntimeError, match="já existe"):
        create(git_repo, "feat-x")
