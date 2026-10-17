"""Make a UTF-8 copy of an old PyInstaller tool (squirrel.exe).
为老的 PyInstaller 工具（squirrel.exe）生成一个使用 UTF-8 的副本。

squirrel was built with Python 3.7, which writes text in the Windows ANSI code page (GBK on
Chinese Windows). Game titles in Korean and other scripts then crash it with UnicodeEncodeError,
and it ignores PYTHONIOENCODING / PYTHONUTF8. Since Windows 10 1903 a program's manifest can
declare activeCodePage=UTF-8, so the copy gets that declaration. The tool itself is not modified.
squirrel 用 Python 3.7 打包，输出文字时使用 Windows 的 ANSI 代码页（中文系统为 GBK）。
遇到韩文等游戏名时会因 UnicodeEncodeError 崩溃，而且它不读 PYTHONIOENCODING / PYTHONUTF8。
Windows 10 1903 起，程序清单（manifest）可以声明 activeCodePage=UTF-8，所以给副本加上这条声明；
原工具本身不做任何修改。

Windows' resource-update API drops data appended after the PE image, which is where PyInstaller
keeps the program, so that overlay is re-attached afterwards.
Windows 的资源更新接口会丢掉 PE 映像之后附加的数据（PyInstaller 把程序放在那里），所以之后要把它补回去。
"""
import ctypes
import shutil
import struct
import sys
from ctypes import wintypes
from pathlib import Path

RT_MANIFEST = 24
_LOAD_AS_DATAFILE = 0x2
_UTF8_SNIPPET = ('  <application xmlns="urn:schemas-microsoft-com:asm.v3">\n'
                 '    <windowsSettings>\n'
                 '      <activeCodePage xmlns="http://schemas.microsoft.com/SMI/2019/WindowsSettings">UTF-8</activeCodePage>\n'
                 '    </windowsSettings>\n'
                 '  </application>\n')

_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_k32.LoadLibraryExW.restype = wintypes.HMODULE
_k32.LoadLibraryExW.argtypes = [wintypes.LPCWSTR, wintypes.HANDLE, wintypes.DWORD]
_k32.FindResourceW.restype = wintypes.HANDLE
_k32.FindResourceW.argtypes = [wintypes.HMODULE, wintypes.LPVOID, wintypes.LPVOID]
_k32.SizeofResource.argtypes = [wintypes.HMODULE, wintypes.HANDLE]
_k32.LoadResource.restype = wintypes.HANDLE
_k32.LoadResource.argtypes = [wintypes.HMODULE, wintypes.HANDLE]
_k32.LockResource.restype = ctypes.c_void_p
_k32.LockResource.argtypes = [wintypes.HANDLE]
_k32.FreeLibrary.argtypes = [wintypes.HMODULE]
_k32.BeginUpdateResourceW.restype = wintypes.HANDLE
_k32.BeginUpdateResourceW.argtypes = [wintypes.LPCWSTR, wintypes.BOOL]
_k32.UpdateResourceW.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.LPVOID, wintypes.WORD,
                                 ctypes.c_void_p, wintypes.DWORD]
_k32.EndUpdateResourceW.argtypes = [wintypes.HANDLE, wintypes.BOOL]


def supports_utf8_codepage() -> bool:
    """activeCodePage needs Windows 10 build 18362 (1903) or newer. / 需要 Windows 10 1903（18362）或更新。"""
    return sys.platform == "win32" and sys.getwindowsversion().build >= 18362


def _read_manifest(path: Path) -> bytes:
    h = _k32.LoadLibraryExW(str(path), None, _LOAD_AS_DATAFILE)
    if not h:
        raise OSError(ctypes.get_last_error(), "LoadLibraryEx failed")
    try:
        r = _k32.FindResourceW(h, ctypes.c_void_p(1), ctypes.c_void_p(RT_MANIFEST))
        if not r:
            raise OSError("no manifest resource")
        size = _k32.SizeofResource(h, r)
        return ctypes.string_at(_k32.LockResource(_k32.LoadResource(h, r)), size)
    finally:
        _k32.FreeLibrary(h)


def _write_manifest(path: Path, data: bytes) -> None:
    h = _k32.BeginUpdateResourceW(str(path), False)
    if not h:
        raise OSError(ctypes.get_last_error(), "BeginUpdateResource failed")
    buf = ctypes.create_string_buffer(data, len(data))
    if not _k32.UpdateResourceW(h, ctypes.c_void_p(RT_MANIFEST), ctypes.c_void_p(1), 0, buf, len(data)):
        err = ctypes.get_last_error()
        _k32.EndUpdateResourceW(h, True)
        raise OSError(err, "UpdateResource failed")
    if not _k32.EndUpdateResourceW(h, False):
        raise OSError(ctypes.get_last_error(), "EndUpdateResource failed")


def _pe_end(data: bytes) -> int:
    """End of the last section's raw data, i.e. where an appended overlay starts.
    最后一个节的原始数据末尾，即附加数据（overlay）的起点。"""
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    sec = pe + 24 + opt
    return max(sum(struct.unpack_from("<II", data, sec + i * 40 + 16)[::-1]) for i in range(nsec))


def make_utf8_copy(src: Path, dst: Path) -> None:
    """Copy src to dst with activeCodePage=UTF-8 added to the manifest; keeps the overlay.
    把 src 复制为 dst，并在清单里加上 activeCodePage=UTF-8；保留附加数据。"""
    orig = src.read_bytes()
    overlay = orig[_pe_end(orig):]
    tmp = dst.with_name(dst.name + ".part")
    shutil.copyfile(src, tmp)
    manifest = _read_manifest(tmp).decode("utf-8")
    if "activeCodePage" not in manifest:
        _write_manifest(tmp, manifest.replace("</assembly>", _UTF8_SNIPPET + "</assembly>").encode("utf-8"))
    patched = tmp.read_bytes()
    image = patched[:_pe_end(patched)]
    tmp.write_bytes(image + overlay)
    if "activeCodePage" not in _read_manifest(tmp).decode("utf-8"):
        raise OSError("manifest update did not stick")
    tmp.replace(dst)
