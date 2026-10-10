"""FAT32 splitting and joining, in pure Python.
纯 Python 实现的 FAT32 分卷拆分与合并。

NSP  -> folder "<name>.nsp" holding parts 00, 01, ... of 0xFFFF0000 bytes,
        with the archive attribute set (what Atmosphère / installers expect).
XCI  -> "<name>.xc0", "<name>.xc1", ... of 0xFFFF8000 bytes (SX / XCI-Cutter style).

NSP → 名为 "<name>.nsp" 的文件夹，内含 00、01…（每卷 0xFFFF0000 字节），并设置存档属性
      （Atmosphère 和安装器要求如此）。
XCI → "<name>.xc0"、"<name>.xc1"…（每卷 0xFFFF8000 字节，SX / XCI-Cutter 格式）。
"""
import ctypes
from pathlib import Path

from .tasks import StepContext

NSP_CHUNK = 0xFFFF0000
XCI_CHUNK = 0xFFFF8000
_BLOCK = 8 * 1024 * 1024
FILE_ATTRIBUTE_ARCHIVE = 0x20


def needs_split(path: Path) -> bool:
    chunk = XCI_CHUNK if path.suffix.lower() == ".xci" else NSP_CHUNK
    return path.stat().st_size > chunk


def _copy_range(src, dst_path: Path, length: int, done: int, total: int, ctx: StepContext) -> int:
    with open(dst_path, "wb") as dst:
        left = length
        while left > 0:
            if ctx.cancelled():
                raise InterruptedError("cancelled")
            buf = src.read(min(_BLOCK, left))
            if not buf:
                break
            dst.write(buf)
            left -= len(buf)
            done += len(buf)
            ctx.progress(done, total)
    return done


def split_file(src: Path, outdir: Path, ctx: StepContext) -> None:
    total = src.stat().st_size
    is_xci = src.suffix.lower() == ".xci"
    chunk = XCI_CHUNK if is_xci else NSP_CHUNK
    if is_xci:
        parts = [outdir / f"{src.stem}.xc{i}" for i in range((total + chunk - 1) // chunk)]
    else:
        folder = outdir / src.name
        folder.mkdir(parents=True, exist_ok=True)
        parts = [folder / f"{i:02d}" for i in range((total + chunk - 1) // chunk)]
    done = 0
    with open(src, "rb") as f:
        for i, part in enumerate(parts):
            ctx.log(f"  → {part.name}")
            done = _copy_range(f, part, chunk, done, total, ctx)
    if not is_xci:
        ctypes.windll.kernel32.SetFileAttributesW(str(outdir / src.name), FILE_ATTRIBUTE_ARCHIVE)
        ctx.log(f"  archive bit set on {src.name}\\")


def join_parts(src: Path, outdir: Path, ctx: StepContext) -> None:
    """src is either a split-NSP folder or the first .xc0 file.
    src 为 NSP 分卷文件夹，或第一个 .xc0 文件。"""
    if src.is_dir():
        parts = sorted((p for p in src.iterdir() if p.is_file() and p.name.isdigit()), key=lambda p: int(p.name))
        out = outdir / src.name
        if not out.suffix:
            out = out.with_suffix(".nsp")
    else:
        stem = src.with_suffix("")
        parts = []
        i = 0
        while (p := Path(f"{stem}.xc{i}")).exists():
            parts.append(p)
            i += 1
        out = outdir / f"{stem.name}.xci"
    if not parts:
        raise FileNotFoundError(f"no parts found in {src}")
    if out.resolve() == src.resolve():
        raise FileExistsError(f"output would overwrite source: {out}")
    total = sum(p.stat().st_size for p in parts)
    done = 0
    with open(out, "wb") as dst:
        for p in parts:
            ctx.log(f"  ← {p.name}")
            with open(p, "rb") as f:
                while buf := f.read(_BLOCK):
                    if ctx.cancelled():
                        raise InterruptedError("cancelled")
                    dst.write(buf)
                    done += len(buf)
                    ctx.progress(done, total)
    ctx.log(f"  = {out}")


def is_split_source(path: Path) -> bool:
    if path.is_dir():
        return any(p.name == "00" for p in path.iterdir())
    return path.suffix.lower() == ".xc0"
