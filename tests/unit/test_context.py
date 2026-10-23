"""Unit tests for Progressive Context Builder and Cache."""

import tempfile
from pathlib import Path
import unittest

from orchestra.context.builder import ContextBuilder
from orchestra.context.cache import ContentCache
from orchestra.registry.discovery import SkillDiscovery


class TestContext(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent.parent.parent
        self.builder = ContextBuilder(self.root)
        self.discovery = SkillDiscovery()
        self.skills = self.discovery.discover_workspace(self.root)

    def test_progressive_layer_assembly(self):
        selected = [self.skills["superpowers"]]
        artifacts = {"ACTIVE_TASK.md": "# Active task\nFix token bug"}

        manifest = self.builder.build_context(
            task="Add new feature",
            selected_skills=selected,
            task_artifacts=artifacts,
            include_l1=True,
        )

        layers = [it.layer for it in manifest.items]
        self.assertIn("L0", layers)
        self.assertIn("L1", layers)
        self.assertIn("L2", layers)
        self.assertIn("L3", layers)

        # L0 must be AGENTS.md, L1 must be ORCHESTRATOR.md, L2 must be superpowers SKILL.md
        paths = {it.layer: it.path for it in manifest.items}
        self.assertEqual(paths["L0"], "AGENTS.md")
        self.assertEqual(paths["L1"], "ORCHESTRATOR.md")
        self.assertEqual(paths["L2"], "skills/superpowers/SKILL.md")
        self.assertEqual(paths["L3"], "ACTIVE_TASK.md")

    def test_token_estimation(self):
        sample = "The quick brown fox jumps over the lazy dog."
        est = self.builder.estimate_tokens(sample)
        self.assertGreater(est, 0)
        self.assertLess(est, 50)

    def test_content_cache_invalidation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache = ContentCache(tmp_dir)
            key = "sample_file.txt"
            content_v1 = "version 1 content"
            hash_v1 = self.builder.hash_content(content_v1)

            cache.set(key, {"parsed": "data_v1"}, content_hash=hash_v1)
            # Retrieve with matching hash
            res = cache.get(key, expected_content_hash=hash_v1)
            self.assertEqual(res, {"parsed": "data_v1"})

            # Retrieve with changed hash -> returns None (stale invalidation)
            hash_v2 = self.builder.hash_content("version 2 content")
            self.assertIsNone(cache.get(key, expected_content_hash=hash_v2))


if __name__ == "__main__":
    unittest.main()
