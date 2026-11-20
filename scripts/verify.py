from __future__ import annotations

import compileall
import json
import struct
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
assert manifest["version"] == "0.2.2"
assert (ROOT / "hacs.json").is_file()
assert "Apache License" in (ROOT / "LICENSE").read_text(encoding="utf-8")
assert "Puzzary contributors" in (ROOT / "NOTICE").read_text(encoding="utf-8")
assert (ROOT / "CONTRIBUTING.md").is_file()
assert (ROOT / "SECURITY.md").is_file()

brand = COMPONENT / "brand"
expected_brand_images = {"icon.png": (256, 256), "icon@2x.png": (512, 512)}
for filename, expected_size in expected_brand_images.items():
    data = (brand / filename).read_bytes()
    assert data.startswith(b"\x89PNG\r\n\x1a\n"), filename
    assert struct.unpack(">II", data[16:24]) == expected_size, filename
    assert data[25] == 6, f"{filename} must preserve RGBA transparency"
assert not (brand / "dark_icon.png").exists()
assert (ROOT / "branding" / "puzzary-mark.svg").is_file()
assert "#0d3b36" in (ROOT / "branding" / "puzzary-mark.svg").read_text(encoding="utf-8")
assert "python scripts/export_brand_assets.py" in (ROOT / "branding" / "README.md").read_text(encoding="utf-8")
assert "2026.3 and newer" in (ROOT / "README.md").read_text(encoding="utf-8")

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
print("Puzzary Home Assistant package structure, branding, actions, translations, and Python compilation passed.")

