"""Unit tests for Skill Registry, Discovery, and Deterministic Routing."""

from pathlib import Path
import unittest

from orchestra.models import Tier
from orchestra.registry import SkillDiscovery, SkillResolver, RoutingExplainer


class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent.parent.parent
        self.discovery = SkillDiscovery()
        self.skills = self.discovery.discover_workspace(self.root)
        self.resolver = SkillResolver(self.skills)

    def test_discovery_finds_all_skills(self):
        self.assertGreaterEqual(len(self.skills), 8)
        self.assertIn("caveman", self.skills)
        self.assertIn("superpowers", self.skills)
        self.assertIn("impeccable", self.skills)
        self.assertIn("graphify", self.skills)

    def test_deterministic_routing_reproducibility(self):
        task = "Add JWT token refresh endpoint in auth/router.py"
        res1 = self.resolver.resolve(task)
        res2 = self.resolver.resolve(task)

        # Same inputs must produce exact same deterministic decisions
        self.assertEqual(res1.inferred_tier, res2.inferred_tier)
        self.assertEqual([s.id for s in res1.selected_skills], [s.id for s in res2.selected_skills])
        self.assertEqual(res1.estimated_context_tokens, res2.estimated_context_tokens)

    def test_explicit_skill_invocation(self):
        task = "Use /impeccable to format this navigation menu"
        res = self.resolver.resolve(task)
        selected_ids = [s.id for s in res.selected_skills]
        self.assertIn("impeccable", selected_ids)

    def test_tier_inference(self):
        self.assertEqual(self.resolver._infer_tier("Fix typo in docstring"), Tier.TINY)
        self.assertEqual(self.resolver._infer_tier("Add search filter button"), Tier.NORMAL)
        self.assertEqual(self.resolver._infer_tier("Cross-module auth token migration"), Tier.COMPLEX)
        self.assertEqual(self.resolver._infer_tier("Architectural redesign of persistence store"), Tier.ARCHITECTURAL)

    def test_cycle_detection(self):
        # Artificially inject cyclic dependency
        cyclic_skills = dict(self.skills)
        s1 = cyclic_skills["superpowers"]
        s2 = cyclic_skills["impeccable"]

        # Mutate dependencies to introduce cycle: superpowers -> impeccable -> superpowers
        from orchestra.models import SkillManifest
        c_s1 = SkillManifest(
            schema_version=s1.schema_version, id=s1.id, name=s1.name, version=s1.version,
            kind=s1.kind, summary=s1.summary, triggers=s1.triggers, capabilities=s1.capabilities,
            dependencies=["impeccable"], path=s1.path,
        )
        c_s2 = SkillManifest(
            schema_version=s2.schema_version, id=s2.id, name=s2.name, version=s2.version,
            kind=s2.kind, summary=s2.summary, triggers=s2.triggers, capabilities=s2.capabilities,
            dependencies=["superpowers"], path=s2.path,
        )
        cyclic_skills["superpowers"] = c_s1
        cyclic_skills["impeccable"] = c_s2

        cyclic_resolver = SkillResolver(cyclic_skills)
        with self.assertRaises(ValueError) as ctx:
            cyclic_resolver.resolve("/superpowers build UI")
        self.assertIn("cycle detected", str(ctx.exception).lower())

    def test_explainer_output(self):
        res = self.resolver.resolve("Explore unfamiliar codebase architecture")
        text = RoutingExplainer.format_text(res)
        self.assertIn("Orchestra Routing Explanation", text)
        self.assertIn("Task:", text)
        self.assertIn("Ambient Session Skills", text)

        d = RoutingExplainer.to_dict(res)
        self.assertIn("task", d)
        self.assertIn("selected_skills", d)


if __name__ == "__main__":
    unittest.main()
