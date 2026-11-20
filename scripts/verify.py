from __future__ import annotations

import compileall
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "puzzary"

manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
translations = json.loads((COMPONENT / "translations" / "en.json").read_text(encoding="utf-8"))
services = yaml.safe_load((COMPONENT / "services.yaml").read_text(encoding="utf-8"))

assert manifest["domain"] == "puzzary"
assert manifest["config_flow"] is True
assert manifest["documentation"] == "https://github.com/barrelcollector/puzzary-home-assistant"
assert manifest["dependencies"] == ["http", "media_source"]
assert manifest["version"] == "0.2.1"
assert (ROOT / "hacs.json").is_file()
assert "Apache License" in (ROOT / "LICENSE").read_text(encoding="utf-8")
assert "Puzzary contributors" in (ROOT / "NOTICE").read_text(encoding="utf-8")
assert (ROOT / "CONTRIBUTING.md").is_file()
assert (ROOT / "SECURITY.md").is_file()

required = (
    "__init__.py", "api.py", "config_flow.py", "coordinator.py", "entity.py",
    "sensor.py", "image.py", "media_source.py", "services.yaml",
)
for filename in required:
    assert (COMPONENT / filename).is_file(), filename

for service in ("refresh", "generate_puzzle", "publish_puzzle", "archive_puzzle", "unarchive_puzzle"):
    assert service in strings["services"]
    assert service in translations["services"]
    assert service in services
    assert set(services[service]["fields"]) == set(translations["services"][service]["fields"])

assert compileall.compile_dir(COMPONENT, quiet=1)
print("Puzzary Home Assistant package structure, actions, translations, and Python compilation passed.")

