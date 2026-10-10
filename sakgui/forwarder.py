"""NRO forwarder helpers: read NRO assets, build NACP, lay out hacBrewPack input dirs.
NRO 转发器辅助函数：读取 NRO 资源、生成 NACP、准备 hacBrewPack 的输入目录。

Layout handed to hacBrewPack:
    exefs/main, exefs/main.npdm      nx-hbloader forwarder build (from SAK bin: nro_fw_main*)
    romfs/nextNroPath, nextArgv      "sdmc:/switch/foo.nro" — read by the forwarder at boot
    control/control.nacp             built here
    control/icon_<Language>.dat      256x256 baseline JPEG, one per language
    logo/NintendoLogo.png, StartupMovie.gif
hacBrewPack --titleid patches the title id into npdm and nacp.
hacBrewPack 的 --titleid 参数会把 Title ID 写入 npdm 和 nacp。
"""
import io
import random
import shutil
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image

LANGUAGES = [
    "AmericanEnglish", "BritishEnglish", "Japanese", "French", "German",
    "LatinAmericanSpanish", "Spanish", "Italian", "Dutch", "CanadianFrench",
    "Portuguese", "Russian", "Korean", "TraditionalChinese", "SimplifiedChinese",
    "BrazilianPortuguese",
]

# NACP field offsets (switchbrew "NACP Format") / NACP 字段偏移（参见 switchbrew "NACP Format"）
_TITLE_SIZE = 0x300
_STARTUP_USER = 0x3025
_SUPPORTED_LANG = 0x302C
_SCREENSHOT = 0x3034
_VIDEO = 0x3035
_RATING_AGE = 0x3040
_DISPLAY_VERSION = 0x3060


@dataclass
class NroInfo:
    name: str = ""
    publisher: str = ""
    version: str = ""
    icon: Optional[bytes] = None


def _cstr(b: bytes) -> str:
    return b.split(b"\0", 1)[0].decode("utf-8", errors="replace")


def read_nro(path: Path) -> NroInfo:
    """Read title/publisher/version/icon from the ASET section appended to an NRO.
    从 NRO 末尾的 ASET 段读取名称、发行者、版本和图标。"""
    info = NroInfo()
    with open(path, "rb") as f:
        head = f.read(0x80)
        if head[0x10:0x14] != b"NRO0":
            raise ValueError("not an NRO file")
        nro_size = struct.unpack_from("<I", head, 0x18)[0]
        f.seek(nro_size)
        aset = f.read(0x38)
        if aset[:4] != b"ASET":
            return info
        icon_off, icon_size, nacp_off, nacp_size = struct.unpack_from("<QQQQ", aset, 0x8)
        if icon_size:
            f.seek(nro_size + icon_off)
            info.icon = f.read(icon_size)
        if nacp_size >= 0x3070:
            f.seek(nro_size + nacp_off)
            nacp = f.read(nacp_size)
            info.name = _cstr(nacp[0:0x200])
            info.publisher = _cstr(nacp[0x200:0x300])
            info.version = _cstr(nacp[_DISPLAY_VERSION:_DISPLAY_VERSION + 0x10])
    return info


def random_title_id() -> str:
    # 05xxxxxxxxxxx000 — homebrew range, low 12 bits clear like a real application id
    # 05xxxxxxxxxxx000 —— 自制软件常用范围，低 12 位为 0，与正式应用 ID 格式一致
    return "05" + "".join(random.choice("0123456789ABCDEF") for _ in range(11)) + "000"


def build_nacp(name: str, publisher: str, version: str,
               screenshot: bool, video: bool, startup_user: bool) -> bytes:
    b = bytearray(0x4000)
    n = name.encode("utf-8")[:0x1FF]
    p = publisher.encode("utf-8")[:0xFF]
    for i in range(len(LANGUAGES)):
        o = i * _TITLE_SIZE
        b[o:o + len(n)] = n
        b[o + 0x200:o + 0x200 + len(p)] = p
    b[_STARTUP_USER] = 1 if startup_user else 0
    struct.pack_into("<I", b, _SUPPORTED_LANG, (1 << len(LANGUAGES)) - 1)
    b[_SCREENSHOT] = 0 if screenshot else 1   # 0 = allow 允许, 1 = deny 禁止
    b[_VIDEO] = 2 if video else 0             # 2 = enabled 开启, 0 = disabled 关闭
    b[_RATING_AGE:_RATING_AGE + 0x20] = b"\xff" * 0x20
    v = version.encode("utf-8")[:0xF]
    b[_DISPLAY_VERSION:_DISPLAY_VERSION + len(v)] = v
    return bytes(b)


def icon_jpeg(source) -> bytes:
    """source: path or raw image bytes. Returns a 256x256 baseline JPEG without EXIF.
    source：图片路径或原始字节。返回不含 EXIF 的 256×256 基线 JPEG。"""
    img = Image.open(io.BytesIO(source) if isinstance(source, (bytes, bytearray)) else source)
    img = img.convert("RGB").resize((256, 256), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, "JPEG", quality=95, progressive=False, optimize=False)
    return out.getvalue()


def prepare_build_dir(build: Path, tools_dir: Path, nro_sd_path: str, nacp: bytes, icon: bytes) -> None:
    if build.exists():
        shutil.rmtree(build)
    exefs, romfs, control, logo = (build / d for d in ("exefs", "romfs", "control", "logo"))
    for d in (exefs, romfs, control, logo):
        d.mkdir(parents=True)
    shutil.copyfile(tools_dir / "nro_fw_main", exefs / "main")
    shutil.copyfile(tools_dir / "nro_fw_main.npdm", exefs / "main.npdm")
    (romfs / "nextNroPath").write_bytes(nro_sd_path.encode("utf-8"))
    (romfs / "nextArgv").write_bytes(nro_sd_path.encode("utf-8"))
    (control / "control.nacp").write_bytes(nacp)
    for lang in LANGUAGES:
        (control / f"icon_{lang}.dat").write_bytes(icon)
    for src, dst in (("nro_fw_NintendoLogo.png", "NintendoLogo.png"),
                     ("nro_fw_StartupMovie.gif", "StartupMovie.gif")):
        if (tools_dir / src).exists():
            shutil.copyfile(tools_dir / src, logo / dst)
