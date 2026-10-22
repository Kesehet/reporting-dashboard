"""Regression checks for the release builder (no database or PyInstaller build needed)."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "api-server" / "build" / "generate_build.py"
spec = importlib.util.spec_from_file_location("report_build_script", SCRIPT)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class BuildPipelineTests(unittest.TestCase):
    def test_all_three_worker_entrypoints_present(self):
        self.assertEqual(set(builder.ENTRYPOINTS), {"serve", "cache_gen", "csvLoader"})
        for name in builder.ENTRYPOINTS:
            self.assertTrue((builder.API_DIR / (name + ".py")).is_file())

    def test_python_modules_are_collected_including_nested_reporting_features(self):
        modules = set(builder.bundled_modules())
        self.assertIn("report_modules.businessAccountsSummary", modules)
        self.assertIn("report_modules.condition_utils", modules)
        self.assertIn("report_generators.loan_commitments_generator", modules)
        self.assertIn("helper.encryption_helper", modules)

    def test_each_command_includes_runtime_hook_and_dynamic_modules(self):
        for name in builder.ENTRYPOINTS:
            with self.subTest(name=name):
                cmd, executable = builder.pyinstaller_command(name, ["pyodbc"])
                self.assertIn("--onefile", cmd)
                self.assertIn("--runtime-hook", cmd)
                self.assertIn("--paths", cmd)
                self.assertIn("Crypto.Cipher.AES", cmd)
                self.assertIn("openpyxl.reader.excel", cmd)
                self.assertIn("report_modules.businessAccountsSummary", cmd)
                self.assertIn("pyodbc", cmd)
                self.assertEqual(executable.name, name + (".exe" if builder.os.name == "nt" else ""))

    def test_invalid_worker_is_rejected(self):
        with self.assertRaises(ValueError):
            builder.pyinstaller_command("unknown", [])

    def test_source_audit_rejects_missing_deep_import(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "new_report.py"
            source.write_text("def late_path():\n    import synthetic_module_not_installed_7ce4\n")
            with mock.patch.object(builder, "runtime_sources", return_value=[source]), \
                 mock.patch.object(builder, "bundled_modules", return_value=["new_report"]):
                with self.assertRaisesRegex(RuntimeError, "synthetic_module_not_installed_7ce4"):
                    builder.verify_python_sources()

    def test_source_audit_detects_syntax_error(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "broken.py"
            source.write_text("def broken(: pass")
            with mock.patch.object(builder, "runtime_sources", return_value=[source]), \
                 mock.patch.object(builder, "bundled_modules", return_value=["broken"]):
                with self.assertRaisesRegex(RuntimeError, "broken.py"):
                    builder.verify_python_sources()

    def test_missing_pinned_requirement_is_fatal(self):
        with TemporaryDirectory() as directory:
            Path(directory, "requirements.txt").write_text("definitely-nonexistent-build-package==1.2.3\n")
            with mock.patch.object(builder, "ROOT", Path(directory)):
                with self.assertRaisesRegex(RuntimeError, "definitely-nonexistent-build-package"):
                    builder.verify_requirements()

    def test_frozen_smoke_must_emit_explicit_success_marker(self):
        with mock.patch.object(builder, "run", return_value=SimpleNamespace(stdout="startup failed", stderr="")):
            with self.assertRaisesRegex(RuntimeError, "Frozen smoke did not complete"):
                builder.frozen_smoke(Path("fake_serve.exe"))
        with mock.patch.object(builder, "run", return_value=SimpleNamespace(stdout="BUILD-SMOKE-OK", stderr="")):
            builder.frozen_smoke(Path("fake_serve.exe"))

    def test_old_binary_cannot_mask_a_failed_freeze(self):
        with TemporaryDirectory() as directory:
            with mock.patch.object(builder, "DIST_DIR", Path(directory)), \
                 mock.patch.object(builder, "verify_python_sources", return_value=[]), \
                 mock.patch.object(builder, "run", side_effect=RuntimeError("PyInstaller crashed")):
                old_binary = Path(directory) / ("serve.exe" if builder.os.name == "nt" else "serve")
                old_binary.write_bytes(b"stale")
                with self.assertRaisesRegex(RuntimeError, "PyInstaller crashed"):
                    builder.build("serve")
                self.assertFalse(old_binary.exists())
                self.assertFalse((Path(directory) / "build-report.json").exists())


if __name__ == "__main__":
    unittest.main()
