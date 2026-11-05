import ast
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / "blender" / "render_shots.py"


def load_write_times():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "write_times"
    )
    code = compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), "exec")
    namespace = {"json": json, "os": os, "tempfile": tempfile}
    exec(code, namespace)
    return namespace["write_times"]


class WriteTimesTests(unittest.TestCase):
    def test_new_times_merge_with_prior_entries(self):
        write_times = load_write_times()
        prior = {"prior-shot": {"seconds": 12.0}, "current-shot": {"seconds": 2.0}}
        updated = {"prior-shot": {"seconds": 12.0}, "current-shot": {"seconds": 4.0}}

        with tempfile.TemporaryDirectory(prefix="chasm-times-test-") as temp:
            journal = Path(temp) / "times.json"
            journal.write_text(json.dumps(prior), encoding="utf-8")

            write_times(temp, {"current-shot": {"seconds": 4.0}})

            self.assertEqual(json.loads(journal.read_text(encoding="utf-8")), updated)

    def test_interrupted_write_preserves_the_previous_journal(self):
        write_times = load_write_times()
        prior = {"prior-shot": {"seconds": 12.0}}

        with tempfile.TemporaryDirectory(prefix="chasm-times-test-") as temp:
            journal = Path(temp) / "times.json"
            journal.write_text(json.dumps(prior), encoding="utf-8")

            def interrupt_after_partial_write(data, file, indent):
                file.write("{")
                file.flush()
                raise InterruptedError("process stopped during JSON write")

            with patch.object(json, "dump", side_effect=interrupt_after_partial_write):
                with self.assertRaises(InterruptedError):
                    write_times(temp, {"current-shot": {"seconds": 4.0}})

            self.assertEqual(json.loads(journal.read_text(encoding="utf-8")), prior)
            self.assertEqual({path.name for path in Path(temp).iterdir()}, {"times.json"})

    def test_invalid_journal_is_not_overwritten(self):
        write_times = load_write_times()
        invalid = "{"

        with tempfile.TemporaryDirectory(prefix="chasm-times-test-") as temp:
            journal = Path(temp) / "times.json"
            journal.write_text(invalid, encoding="utf-8")

            with self.assertRaises(json.JSONDecodeError):
                write_times(temp, {"current-shot": {"seconds": 4.0}})

            self.assertEqual(journal.read_text(encoding="utf-8"), invalid)


if __name__ == "__main__":
    unittest.main()
