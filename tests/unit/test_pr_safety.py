"""Unit tests for WorkspaceSafetyWrapper and rollback traps."""

import unittest
from unittest.mock import MagicMock, patch

from orchestra.pr.safety import WorkspaceSafetyError, WorkspaceSafetyWrapper


class TestWorkspaceSafety(unittest.TestCase):
    def setUp(self):
        self.safety = WorkspaceSafetyWrapper()

    @patch("subprocess.run")
    def test_verify_tooling_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        # Should not raise
        self.safety.verify_tooling()

    @patch("pathlib.Path.exists")
    @patch("subprocess.run")
    def test_verify_tooling_gh_not_authenticated(self, mock_run, mock_exists):
        mock_exists.return_value = False
        mock_run.side_effect = [
            MagicMock(returncode=0),  # git --version
            MagicMock(returncode=1, stderr="You are not logged in"),  # gh auth status
        ]
        with self.assertRaises(WorkspaceSafetyError):
            self.safety.verify_tooling()

    @patch.object(WorkspaceSafetyWrapper, "verify_tooling")
    @patch.object(WorkspaceSafetyWrapper, "_run_git")
    def test_capture_snapshot_clean_tree(self, mock_git, mock_tooling):
        mock_git.side_effect = [
            (0, "main"),          # symbolic-ref HEAD
            (0, "abcdef123456"),  # rev-parse HEAD
            (0, ""),              # status --porcelain (clean)
        ]
        snapshot = self.safety.capture_snapshot()
        self.assertEqual(snapshot.original_branch, "main")
        self.assertEqual(snapshot.original_sha, "abcdef123456")
        self.assertFalse(snapshot.stash_pushed)

    @patch.object(WorkspaceSafetyWrapper, "verify_tooling")
    @patch.object(WorkspaceSafetyWrapper, "_run_git")
    def test_capture_snapshot_dirty_tree_stashes(self, mock_git, mock_tooling):
        mock_git.side_effect = [
            (0, "feature-x"),     # symbolic-ref HEAD
            (0, "commit123456"),  # rev-parse HEAD
            (0, " M modified.py\n?? untracked.txt"),  # status --porcelain (dirty)
            (0, "Saved working directory and index state"),  # stash push
        ]
        snapshot = self.safety.capture_snapshot()
        self.assertEqual(snapshot.original_branch, "feature-x")
        self.assertTrue(snapshot.stash_pushed)
        self.assertIsNotNone(snapshot.stash_ref)

    @patch.object(WorkspaceSafetyWrapper, "_run_git")
    def test_restore_pops_stash_and_checks_out_branch(self, mock_git):
        mock_git.side_effect = [
            (0, "Switched to branch 'feature-x'"),  # git checkout
            (0, "Applied stash"),                   # git stash pop
        ]
        self.safety.snapshot = self.safety.capture_snapshot.__func__(
            self.safety
        ) if False else None

        from orchestra.pr.models import WorkspaceSnapshot
        self.safety.snapshot = WorkspaceSnapshot(
            original_branch="feature-x",
            original_sha="commit123456",
            stash_pushed=True,
            stash_ref="test-stash",
        )
        self.safety.restore()
        self.assertEqual(mock_git.call_count, 2)
        mock_git.assert_any_call(["checkout", "feature-x"])
        mock_git.assert_any_call(["stash", "pop"])


    @patch.object(WorkspaceSafetyWrapper, "_run_git")
    def test_restore_conflict_raises_tier1_blocker(self, mock_git):
        from orchestra.pr.safety import GitConflictBlockerError
        mock_git.side_effect = [
            (0, "Switched to branch 'feature-x'"),
            (1, "CONFLICT (content): Merge conflict in file.py"),
        ]
        from orchestra.pr.models import WorkspaceSnapshot
        self.safety.snapshot = WorkspaceSnapshot(
            original_branch="feature-x",
            original_sha="commit123456",
            stash_pushed=True,
            stash_ref="test-stash",
        )
        with self.assertRaises(GitConflictBlockerError):
            self.safety.restore()


if __name__ == "__main__":
    unittest.main()
