"""Permisos locales independientes de las anotaciones del servidor."""
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
from harness.mcp_policy import prepare_call, filter_result


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


class FilesystemPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()

    def test_block_all_paths_and_protected_files(self):
        for path in ("../outside", ".env", "a/credentials.json", "mcp.json", ".git/config", ".harness_sessions/one.json", "file.txt:secret"):
            with self.subTest(path=path), self.assertRaises(PermissionError):
                prepare_call("filesystem", "read_multiple_files", {"paths": ["ok.txt", path]}, self.base)

    def test_symlink_outside_is_rejected(self):
        link = self.base / "escape"
        try:
            link.symlink_to(self.base.parent, target_is_directory=True)
        except OSError:
            self.skipTest("Crear symlinks requiere privilegio de Windows o Developer Mode")
        with self.assertRaises(PermissionError):
            prepare_call("filesystem", "read_text_file", {"path": "escape/secret.txt"}, self.base)

    def test_confirm_and_deny_write(self):
        args = {"path": "demo.txt", "content": "hola"}
        with self.assertRaises(PermissionError):
            prepare_call("filesystem", "write_file", args, self.base, lambda *_: False)
        prepared = prepare_call("filesystem", "write_file", args, self.base, lambda *_: True)
        self.assertEqual(prepared["path"], str(self.base / "demo.txt"))
        self.assertFalse((self.base / "demo.txt").exists())  # La política no escribe.

    def test_list_and_search_filter_secrets(self):
        text = "[FILE] .env\n[FILE] app.py\n[DIR] .git\n[DIR] src"
        self.assertEqual(filter_result("filesystem", "list_directory", text,
            {"path": str(self.base)}, self.base), "[FILE] app.py\n[DIR] src")
        text = str(self.base / ".env") + "\n" + str(self.base / "app.py")
        self.assertEqual(filter_result("filesystem", "search_files", text, {}, self.base), str(self.base / "app.py"))


if __name__ == "__main__":
    unittest.main()
