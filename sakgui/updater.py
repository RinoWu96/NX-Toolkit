"""Download / update the external tools and check for a newer NX Toolkit.
下载 / 更新外部工具，并检查 NX Toolkit 是否有新版本。

Tools come from the original SAK release (dezem/SAK on GitHub), which bundles every CLI tool
this program drives. Key files are never extracted or overwritten.
工具来自原版 SAK 的发布包（GitHub 上的 dezem/SAK），其中带齐了本程序调用的所有命令行工具。
密钥文件永远不会被解压或覆盖。
"""
import json
import shutil
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

import py7zr

from . import __version__
from .tasks import StepContext

SAK_RELEASES = "https://api.github.com/repos/dezem/SAK/releases/latest"
APP_RELEASES = "https://api.github.com/repos/RinoWu96/NX-Toolkit/releases/latest"
APP_PAGE = "https://github.com/RinoWu96/NX-Toolkit/releases/latest"
VERSION_FILE = "tools_version.txt"  # which SAK release the tools came from / 工具来自哪个 SAK 版本
_KEY_NAMES = {"prod.keys", "keys.txt", "keys.dat", "title.keys"}
_UA = {"User-Agent": f"NX-Toolkit/{__version__}"}


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={**_UA, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def _version_tuple(v: str) -> Tuple[int, ...]:
    return tuple(int(x) for x in v.lstrip("vV").split(".") if x.isdigit())


def latest_sak() -> Tuple[str, str, int]:
    """(tag, download url, size) of the 64-bit SAK archive. / 64 位 SAK 压缩包的（版本, 下载地址, 大小）。"""
    rel = _get_json(SAK_RELEASES)
    for a in rel.get("assets", []):
        if "64bit" in a["name"] and a["name"].endswith(".7z"):
            return rel["tag_name"], a["browser_download_url"], a["size"]
    raise RuntimeError("no 64-bit .7z asset in the latest SAK release")


def installed_tools_version(tools_dir: Path) -> str:
    f = tools_dir / VERSION_FILE
    return f.read_text(encoding="utf-8").strip() if f.is_file() else ""


def latest_app() -> Optional[str]:
    """Tag of the newest NX Toolkit release if it is newer than this build, else None.
    如果有比当前更新的 NX Toolkit 版本则返回其版本号，否则返回 None。"""
    tag = _get_json(APP_RELEASES)["tag_name"]
    return tag if _version_tuple(tag) > _version_tuple(__version__) else None


def _download(url: str, dest: Path, size: int, ctx: StepContext) -> None:
    req = urllib.request.Request(url, headers=_UA)
    done = 0
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        total = int(r.headers.get("Content-Length") or size or 0)
        while chunk := r.read(256 * 1024):
            if ctx.cancelled():
                raise InterruptedError("cancelled")
            f.write(chunk)
            done += len(chunk)
            ctx.progress(done, total)


def install_tools(tools_dir: Path, work: Path, ctx: StepContext, log) -> str:
    """Download the latest SAK release and copy its bin/ into tools_dir (keys excluded).
    下载最新的 SAK 发布包，把其中 bin/ 的内容复制到 tools_dir（不含密钥）。Returns the SAK tag."""
    tag, url, size = latest_sak()
    log("sak_found", tag, f"{size / 1024 / 1024:.1f} MB")
    archive = work / Path(url).name
    _download(url, archive, size, ctx)
    log("extracting")
    ctx.progress(0, 0)
    out = work / "x"
    with py7zr.SevenZipFile(archive) as z:
        z.extractall(out)
    bins = list(out.glob("*/bin"))
    if not bins:
        raise RuntimeError("bin folder not found in archive")
    tools_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in bins[0].iterdir():
        if not f.is_file() or f.name.lower() in _KEY_NAMES:
            continue
        shutil.copyfile(f, tools_dir / f.name)
        n += 1
    (tools_dir / VERSION_FILE).write_text(tag, encoding="utf-8")
    log("tools_installed", n, tools_dir)
    return tag
