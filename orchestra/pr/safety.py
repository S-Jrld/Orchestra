"""Fail-safe workspace state management and rollback traps for PR checkout."""

from __future__ import annotations

import datetime
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from orchestra.pr.models import WorkspaceSnapshot


class WorkspaceSafetyError(Exception):
    """Raised when pre-flight checks fail or workspace operations risk data loss."""
    pass


class GitConflictBlockerError(WorkspaceSafetyError):
    """Tier 1 Blocker: Unresolvable git merge conflict during checkout or stash restore."""
    pass


class WorkspaceSafetyWrapper:
    """Guarantees pre-flight state preservation, dirty stashing, and safe rollback."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self.snapshot: Optional[WorkspaceSnapshot] = None
        self._cleaned_up = False

    def _get_clean_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["GIT_PAGER"] = "cat"
        env["GH_PAGER"] = "cat"
        bin_dir = str(self.workspace_root / "bin")
        local_bin = str(Path.home() / ".local" / "bin")
        env["PATH"] = f"{bin_dir}:{local_bin}:{env.get('PATH', '')}"
        return env

    def _run_git(self, args: list[str]) -> tuple[int, str]:
        cmd = ["git"] + args
        try:
            res = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=False,
                env=self._get_clean_env(),
            )
            output = (res.stdout + "\n" + res.stderr).strip()
            return res.returncode, output
        except Exception as e:
            return 1, f"Git execution failed: {str(e)}"

    def verify_tooling(self) -> None:
        """Verifies git and gh CLI are installed and gh is authenticated via non-interactive call."""
        git_code, _ = self._run_git(["--version"])
        if git_code != 0:
            raise WorkspaceSafetyError("Git binary is not available or non-functional.")

        env = self._get_clean_env()
        gh_bin = "gh"
        if not shutil.which("gh", path=env.get("PATH")):
            if (self.workspace_root / "bin" / "gh").exists():
                gh_bin = str(self.workspace_root / "bin" / "gh")
            else:
                raise WorkspaceSafetyError("GitHub CLI ('gh') is not installed in PATH.")

        try:
            gh_res = subprocess.run(
                [gh_bin, "auth", "status"],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            # If status returns 0 or hosts.yml has active token:
            if gh_res.returncode != 0:
                hosts_file = Path.home() / ".config" / "gh" / "hosts.yml"
                if hosts_file.exists() and "oauth_token:" in hosts_file.read_text(encoding="utf-8", errors="ignore"):
                    return
                raise WorkspaceSafetyError(
                    f"GitHub CLI is not authenticated. Please run 'gh auth login'. Output: {gh_res.stderr.strip()}"
                )
        except FileNotFoundError:
            raise WorkspaceSafetyError("GitHub CLI ('gh') is not installed in PATH.")

    def capture_snapshot(self) -> WorkspaceSnapshot:
        """Captures active branch, HEAD commit, and stashes uncommitted modifications."""
        self.verify_tooling()

        # 1. Determine active branch using rev-parse --abbrev-ref HEAD
        code, branch = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if code != 0:
            raise WorkspaceSafetyError(f"Could not determine current git branch: {branch}")

        # 2. Determine HEAD commit SHA
        code, sha = self._run_git(["rev-parse", "HEAD"])
        if code != 0:
            raise WorkspaceSafetyError(f"Could not determine current commit SHA: {sha}")

        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # 3. Check dirty state via git status --porcelain
        code, status_out = self._run_git(["status", "--porcelain"])
        if code != 0:
            raise WorkspaceSafetyError(f"Could not check git status: {status_out}")

        stash_pushed = False
        stash_ref: Optional[str] = None

        if status_out.strip():
            stash_msg = "orchestra-pr-review-snapshot"
            scode, sout = self._run_git(["stash", "push", "-u", "-m", stash_msg])
            if scode != 0:
                raise WorkspaceSafetyError(f"Failed to stash local changes safely: {sout}")
            stash_pushed = True
            stash_ref = stash_msg

        self.snapshot = WorkspaceSnapshot(
            original_branch=branch.strip(),
            original_sha=sha.strip(),
            stash_pushed=stash_pushed,
            stash_ref=stash_ref,
            timestamp=timestamp,
        )
        self._cleaned_up = False
        return self.snapshot

    def restore(self) -> None:
        """Rolls back the workspace to the captured snapshot and restores stashed changes."""
        if not self.snapshot or self._cleaned_up:
            return

        # 1. Checkout original branch
        code, out = self._run_git(["checkout", self.snapshot.original_branch])
        if code != 0:
            # Check for conflict
            if "conflict" in out.lower() or "overwritten by checkout" in out.lower():
                raise GitConflictBlockerError(f"Unresolvable checkout conflict returning to '{self.snapshot.original_branch}': {out}")
            # Try checking out by commit SHA if branch name failed
            code, out = self._run_git(["checkout", self.snapshot.original_sha])
            if code != 0:
                raise WorkspaceSafetyError(f"Failed to return to original commit {self.snapshot.original_sha}: {out}")

        # 2. Restore stash if one was created
        if self.snapshot.stash_pushed:
            code, out = self._run_git(["stash", "pop"])
            if code != 0:
                if "conflict" in out.lower():
                    raise GitConflictBlockerError(
                        f"Unresolvable merge conflict popping stash '{self.snapshot.stash_ref}'. Working tree contains conflict markers: {out}"
                    )
                raise WorkspaceSafetyError(
                    f"Warning: Failed to pop stash automatically. Stash is preserved in git stash list. Output: {out}"
                )

        self._cleaned_up = True

    def __enter__(self) -> WorkspaceSnapshot:
        return self.capture_snapshot()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore()
