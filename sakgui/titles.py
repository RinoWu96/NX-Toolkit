"""Read a game's English title from an XCI / NSP and give output files English names.
从 XCI / NSP 读取游戏的英文标题，并把输出文件改为英文文件名。

squirrel names merged files after whichever title it picks from the game's NACP, which can be
Korean or another script (e.g. "페 이 퍼 마 리 오 … [0100A3900C3E2000] [v65536] (1G+1U).xci").
To get the English title we read only the small NCAs out of the container (no full unpack),
let hactoolnet extract their RomFS, and parse control.nacp.
squirrel 用它从 NACP 里挑中的标题命名合并结果，可能是韩文等文字
（如「페 이 퍼 마 리 오 … [0100A3900C3E2000] [v65536] (1G+1U).xci」）。
为取得英文标题，这里只从容器中读出体积很小的 NCA（不解包整个游戏），
交给 hactoolnet 解出 RomFS，再解析 control.nacp。
"""
import re
import shutil
import struct
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

_SMALL_NCA = 32 * 1024 * 1024  # control NCAs are well under this / Control NCA 远小于此
_NO_WINDOW = 0x08000000        # CREATE_NO_WINDOW
_TITLE_ID = re.compile(r"\s*\[[0-9A-Fa-f]{16}\]")
_BAD_CHARS = re.compile(r'[\\/*?"<>|]')

Entry = Tuple[str, int, int]  # (name, absolute offset, size) / （文件名, 绝对偏移, 大小）


def _hfs0(f, base: int) -> List[Entry]:
    """Entries of an HFS0 partition at `base`. / 位于 base 的 HFS0 分区里的文件条目。"""
    f.seek(base)
    magic, n, strsize, _ = struct.unpack("<4sIII", f.read(16))
    if magic != b"HFS0":
        raise ValueError("not HFS0")
    raw = f.read(0x40 * n)
    strings = f.read(strsize)
    data = base + 16 + 0x40 * n + strsize
    out = []
    for i in range(n):
        off, size, name_off = struct.unpack_from("<QQI", raw, i * 0x40)
        name = strings[name_off:strings.index(b"\0", name_off)].decode("utf-8", "replace")
        out.append((name, data + off, size))
    return out


def _pfs0(f) -> List[Entry]:
    """Entries of an NSP (PFS0). / NSP（PFS0）里的文件条目。"""
    f.seek(0)
    magic, n, strsize, _ = struct.unpack("<4sIII", f.read(16))
    if magic != b"PFS0":
        raise ValueError("not PFS0")
    raw = f.read(0x18 * n)
    strings = f.read(strsize)
    data = 16 + 0x18 * n + strsize
    out = []
    for i in range(n):
        off, size, name_off = struct.unpack_from("<QQI", raw, i * 0x18)
        name = strings[name_off:strings.index(b"\0", name_off)].decode("utf-8", "replace")
        out.append((name, data + off, size))
    return out


def list_ncas(path: Path) -> List[Entry]:
    """NCAs inside an XCI (secure partition) or NSP. / XCI（secure 分区）或 NSP 里的 NCA。"""
    with open(path, "rb") as f:
        if path.suffix.lower() == ".xci":
            f.seek(0x100)
            if f.read(4) != b"HEAD":
                raise ValueError("not an XCI")
            f.seek(0x130)
            root = struct.unpack("<Q", f.read(8))[0]
            secure = next((e for e in _hfs0(f, root) if e[0] == "secure"), None)
            if secure is None:
                raise ValueError("no secure partition")
            entries = _hfs0(f, secure[1])
        else:
            entries = _pfs0(f)
    return [e for e in entries if e[0].endswith(".nca") and not e[0].endswith(".cnmt.nca")]


def nacp_titles(nacp: bytes) -> List[str]:
    """The 16 language titles of a NACP (AmericanEnglish first). / NACP 中 16 种语言的标题（美式英语在前）。"""
    return [nacp[i * 0x300:i * 0x300 + 0x200].split(b"\0", 1)[0].decode("utf-8", "replace").strip()
            for i in range(16)]


def english_title(path: Path, hactoolnet: Path, keys: Path, work: Path) -> Optional[str]:
    """American, else British English title of the game in `path`; None if there is none.
    返回游戏的美式英语标题，没有则用英式英语；都没有返回 None。"""
    work.mkdir(parents=True, exist_ok=True)
    candidates = sorted((e for e in list_ncas(path) if e[2] < _SMALL_NCA), key=lambda e: e[2])
    for i, (name, off, size) in enumerate(candidates):
        nca, romfs = work / f"c{i}.nca", work / f"romfs{i}"
        with open(path, "rb") as src, open(nca, "wb") as dst:
            src.seek(off)
            dst.write(src.read(size))
        subprocess.run([str(hactoolnet), "-k", str(keys), "--disablekeywarns", "-t", "nca",
                        "--romfsdir", str(romfs), str(nca)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW)
        nacp = romfs / "control.nacp"
        if nacp.is_file():
            titles = nacp_titles(nacp.read_bytes())
            return titles[0] or titles[1] or None
    return None


def safe_filename(title: str) -> str:
    """Make a title usable in a Windows file name. / 把标题变成可用于 Windows 文件名的形式。"""
    t = title.replace(":", " -")
    t = _BAD_CHARS.sub("", t)
    t = re.sub(r"\s+", " ", t).strip().rstrip(". ")
    return t


def english_name(path: Path, title: str) -> Optional[str]:
    """New file name with the title part (everything before "[titleid]") replaced, or None.
    把文件名中「[titleid]」之前的标题部分换成英文标题；不符合该格式时返回 None。"""
    m = _TITLE_ID.search(path.name)
    if not m:
        return None
    return f"{safe_filename(title)} {path.name[m.start():].lstrip()}"


def rename_english(path: Path, hactoolnet: Path, keys: Path, work: Path) -> Tuple[Path, str]:
    """Rename `path` to its English title. Returns (final path, status: renamed/same/no_title/no_pattern).
    把 path 改为英文标题文件名。返回（最终路径, 状态）。"""
    try:
        title = english_title(path, hactoolnet, keys, work)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if not title:
        return path, "no_title"
    new = english_name(path, title)
    if new is None:
        return path, "no_pattern"
    if new == path.name:
        return path, "same"
    target = path.with_name(new)
    n = 2
    while target.exists():
        target = path.with_name(f"{Path(new).stem} ({n}){Path(new).suffix}")
        n += 1
    path.rename(target)
    return target, "renamed"
