"""Permisos locales independientes de las anotaciones del servidor."""
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
from harness.mcp_policy import prepare_call


class GitPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        (self.base / ".git").mkdir()

    def test_reject_foreign_repository_and_write(self):
        for name, args in (("git_status", {"repo_path": str(self.base.parent)}),
                           ("git_commit", {"repo_path": str(self.base)})):
            with self.subTest(name=name), self.assertRaises((ValueError, PermissionError)):
                prepare_call("git", name, args, self.base)

    def test_log_is_bounded_and_root_is_fixed(self):
        result = prepare_call("git", "git_log", {"max_count": 100}, self.base)
        self.assertEqual(result, {"max_count": 20, "repo_path": str(self.base)})

    def test_diff_never_sends_secret_content(self):
        for path in (b".env\0", b"sub/credentials.json\0", b".harness_session.json\0"):
            with patch("harness.mcp_policy.subprocess.run", return_value=NS(stdout=path)):
                with self.assertRaises(PermissionError):
                    prepare_call("git", "git_diff_unstaged", {}, self.base)
        with patch("harness.mcp_policy.subprocess.run", return_value=NS(stdout=b"app.py\0")):
            self.assertEqual(prepare_call("git", "git_diff_staged", {}, self.base)["context_lines"], 3)


if __name__ == "__main__":
    unittest.main()
