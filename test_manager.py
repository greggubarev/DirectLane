import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).with_name("manager.pyw")
loader = importlib.machinery.SourceFileLoader("directlane", str(SOURCE))
spec = importlib.util.spec_from_loader(loader.name, loader)
app = importlib.util.module_from_spec(spec)
loader.exec_module(app)


class DomainTests(unittest.TestCase):
    def test_normalizes_url_and_idn(self):
        self.assertEqual(app.normalize_domain("https://RU.Wikipedia.org/wiki/Test"), "ru.wikipedia.org")
        self.assertEqual(app.normalize_domain("пример.рф"), "xn--e1afmkfd.xn--p1ai")
        with self.assertRaises(ValueError):
            app.normalize_domain("https://user:pass@example.org")

    def test_physical_default_alone_is_not_a_bypass_rule(self):
        snapshot = {"interface_index": 15, "gateway": "192.168.0.1", "routes": [
            {"prefix": "0.0.0.0/0", "gateway": "192.168.0.1", "interface_index": 15, "metric": 0},
        ]}
        self.assertIsNone(app.direct_cover("195.161.4.88", snapshot))
        snapshot["routes"].append({"prefix": "195.161.4.0/24", "gateway": "192.168.0.1", "interface_index": 15, "metric": 37})
        self.assertEqual(app.direct_cover("195.161.4.88", snapshot), "direct")

    def test_reuses_old_route_and_removes_only_owned_route(self):
        with tempfile.TemporaryDirectory() as temp:
            snapshot = {"interface_index": 15, "interface_guid": "{test}", "interface_name": "Ethernet",
                        "gateway": "192.168.0.1", "routes": [
                            {"prefix": "0.0.0.0/0", "gateway": "192.168.0.1", "interface_index": 15, "metric": 0},
                            {"prefix": "10.0.0.0/1", "gateway": "10.0.0.1", "interface_index": 38, "metric": 1},
                            {"prefix": "185.15.56.0/22", "gateway": "192.168.0.1", "interface_index": 15, "metric": 38},
                        ]}
            calls = []

            def bridge(action, **kwargs):
                calls.append((action, kwargs))
                return snapshot if action == "Snapshot" else "OK"

            with patch.object(app, "STATE_PATH", Path(temp) / "domains.json"), \
                 patch.object(app, "DATA_DIR", Path(temp)), \
                 patch.object(app, "resolve_domain", return_value={"example.org": ["185.15.59.224", "195.161.4.88"]}), \
                 patch.object(app, "run_bridge", side_effect=bridge):
                app.add_or_refresh("example.org")
                state = app.load_state()
                self.assertEqual(set(state["routes"]), {"195.161.4.88"})
                self.assertEqual([c[0] for c in calls].count("Add"), 1)
                app.delete_domain("example.org")
                self.assertEqual([c[0] for c in calls].count("Remove"), 1)
                self.assertEqual(calls[-1][1]["Prefix"], "195.161.4.88/32")
                self.assertFalse(app.load_state()["routes"])


if __name__ == "__main__":
    unittest.main()
