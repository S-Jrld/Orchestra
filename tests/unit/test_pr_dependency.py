"""Unit tests for DependencyGraphTracer."""

import tempfile
import unittest
from pathlib import Path

from orchestra.pr.dependency import DependencyGraphTracer
from orchestra.pr.models import ChangedFile


class TestDependencyGraphTracer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.tracer = DependencyGraphTracer(self.workspace)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_trace_python_imports(self):
        # Create module structure
        (self.workspace / "pkg").mkdir()
        (self.workspace / "pkg" / "__init__.py").write_text("")
        auth_file = self.workspace / "pkg" / "auth.py"
        auth_file.write_text("def authenticate(): pass\n")

        # Downstream caller
        server_file = self.workspace / "server.py"
        server_file.write_text("from pkg.auth import authenticate\nauthenticate()\n")

        changed = [ChangedFile(path="pkg/auth.py", status="modified")]
        impact = self.tracer.trace_impact(changed)

        self.assertIn("pkg/auth.py", impact)
        self.assertIn("server.py", impact["pkg/auth.py"])


if __name__ == "__main__":
    unittest.main()
