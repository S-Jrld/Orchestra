"""Unit tests for PRIngestionPipeline, noise filtering, and metadata extraction."""

import json
import unittest
from unittest.mock import MagicMock, patch

from orchestra.pr.ingestion import PRIngestionError, PRIngestionPipeline


class TestPRIngestion(unittest.TestCase):
    def setUp(self):
        self.ingestion = PRIngestionPipeline()

    def test_noise_filtering(self):
        # Noise files
        self.assertTrue(self.ingestion.is_noise_file("package-lock.json")[0])
        self.assertTrue(self.ingestion.is_noise_file("Frontend/package-lock.json")[0])
        self.assertTrue(self.ingestion.is_noise_file("dist/bundle.min.js")[0])
        self.assertTrue(self.ingestion.is_noise_file("assets/image.png")[0])
        self.assertTrue(self.ingestion.is_noise_file("doc/manual.pdf")[0])
        self.assertTrue(self.ingestion.is_noise_file("vendor/lib/plugin.js")[0])
        self.assertTrue(self.ingestion.is_noise_file("node_modules/axios/index.js")[0])

        # High-signal code files
        self.assertFalse(self.ingestion.is_noise_file("src/auth.py")[0])
        self.assertFalse(self.ingestion.is_noise_file("Frontend/src/App.tsx")[0])
        self.assertFalse(self.ingestion.is_noise_file("tests/unit/test_login.py")[0])

    @patch("subprocess.run")
    def test_fetch_metadata_success(self, mock_run):
        mock_payload = {
            "number": 42,
            "title": "feat: add user authentication",
            "body": "Implements double-blind auth.",
            "author": {"login": "octocat"},
            "baseRefName": "main",
            "headRefName": "feat-auth",
            "headRefOid": "headsha123",
            "commits": [{"messageHeadline": "feat: add auth model"}],
            "files": [
                {"path": "src/auth.py", "additions": 50, "deletions": 5},
                {"path": "package-lock.json", "additions": 1000, "deletions": 0},
            ],
            "url": "https://github.com/foo/bar/pull/42",
        }
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(mock_payload))

        meta = self.ingestion.fetch_metadata(42)
        self.assertEqual(meta.number, 42)
        self.assertEqual(meta.author, "octocat")
        self.assertEqual(meta.base_ref, "main")
        self.assertEqual(len(meta.files), 2)

        # Verify noise filter flag
        auth_file = next(f for f in meta.files if f.path == "src/auth.py")
        lock_file = next(f for f in meta.files if f.path == "package-lock.json")
        self.assertFalse(auth_file.is_filtered)
        self.assertTrue(lock_file.is_filtered)

    @patch("subprocess.run")
    def test_fetch_metadata_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="Not found")
        with self.assertRaises(PRIngestionError):
            self.ingestion.fetch_metadata(999)


if __name__ == "__main__":
    unittest.main()
