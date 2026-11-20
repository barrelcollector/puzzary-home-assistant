from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "puzzary"
DIST = ROOT / "dist"
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)


def add_file(bundle: zipfile.ZipFile, archive_name: str, source: Path) -> None:
    entry = zipfile.ZipInfo(archive_name, FIXED_ZIP_TIME)
    entry.compress_type = zipfile.ZIP_DEFLATED
    entry.external_attr = 0o100644 << 16
    bundle.writestr(entry, source.read_bytes())


def main() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    version = manifest["version"]
    shutil.rmtree(DIST, ignore_errors=True)
    DIST.mkdir()
    archive = DIST / f"puzzary-home-assistant-{version}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for source in sorted(path for path in COMPONENT.rglob("*") if path.is_file()):
            if source.suffix in {".pyc", ".pyo"} or "__pycache__" in source.parts:
                continue
            relative = source.relative_to(ROOT).as_posix()
            add_file(bundle, relative, source)
        add_file(bundle, "LICENSE", ROOT / "LICENSE")
        add_file(bundle, "NOTICE", ROOT / "NOTICE")
    with zipfile.ZipFile(archive) as bundle:
        names = set(bundle.namelist())
        assert "LICENSE" in names and "NOTICE" in names
        assert "custom_components/puzzary/manifest.json" in names
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = f"{digest}  {archive.name}\n"
    (DIST / "SHA256SUMS").write_text(checksum, encoding="utf-8")
    archive.with_suffix(".zip.sha256").write_text(checksum, encoding="utf-8")
    print(f"Built {archive.name} ({digest})")


if __name__ == "__main__":
    main()
