"""Copy license files next to the packaged exe (run by build.bat after PyInstaller).
把许可证文件复制到打包好的 exe 旁边（由 build.bat 在 PyInstaller 之后运行）。

Result / 结果:
    dist/NX-Toolkit/LICENSE                     NX Toolkit (MIT)
    dist/NX-Toolkit/THIRD_PARTY_LICENSES.md     component list / 组件清单
    dist/NX-Toolkit/licenses/LGPL-3.0.txt, GPL-3.0.txt
    dist/NX-Toolkit/licenses/<package>/...      each bundled package's own license files / 各内置包自带的许可证
    dist/NX-Toolkit/licenses/python/LICENSE.txt Python runtime
"""
import importlib.metadata as md
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist" / "NX-Toolkit"

# Packages bundled in the exe (keep in sync with THIRD_PARTY_LICENSES.md).
# exe 内置的包（需与 THIRD_PARTY_LICENSES.md 保持一致）。
PACKAGES = [
    "PySide6", "PySide6_Essentials", "shiboken6", "pillow", "psutil", "setuptools", "packaging",
    "nsz", "zstandard", "backports.zstd", "pycryptodome", "pycryptodomex", "enlighten", "prefixed",
    "jinxed", "ansicon", "blessed", "wcwidth",
    "py7zr", "pybcj", "pyppmd", "inflate64", "multivolumefile", "brotli", "texttable",
]


def _is_license(path: str) -> bool:
    name = Path(path).name.upper()
    return any(k in name for k in ("LICEN", "COPYING", "NOTICE", "AUTHORS"))


def main():
    if not DIST.is_dir():
        sys.exit(f"build output not found: {DIST}")
    lic = DIST / "licenses"
    shutil.rmtree(lic, ignore_errors=True)
    lic.mkdir()
    shutil.copyfile(ROOT / "LICENSE", DIST / "LICENSE")
    shutil.copyfile(ROOT / "THIRD_PARTY_LICENSES.md", DIST / "THIRD_PARTY_LICENSES.md")
    for f in (ROOT / "licenses").glob("*.txt"):
        shutil.copyfile(f, lic / f.name)

    missing = []
    for name in PACKAGES:
        dist = md.distribution(name)
        files = [f for f in (dist.files or []) if ".dist-info" in str(f) and _is_license(str(f))]
        if not files:
            missing.append(name)
            continue
        out = lic / name
        out.mkdir()
        for f in files:
            shutil.copyfile(f.locate(), out / Path(str(f)).name)

    py_lic = Path(sys.base_prefix) / "LICENSE.txt"
    if py_lic.is_file():
        (lic / "python").mkdir()
        shutil.copyfile(py_lic, lic / "python" / "LICENSE.txt")
    else:
        missing.append("python")

    print(f"licenses collected into {lic}")
    if missing:
        # Covered by the full texts in licenses/ and the table in THIRD_PARTY_LICENSES.md.
        # 这些包没有自带许可证文件，由 licenses/ 中的全文和清单中的说明覆盖。
        print("no license file shipped by:", ", ".join(missing))


if __name__ == "__main__":
    main()
