"""Persistent settings stored next to the app as config.json.
程序设置，以 config.json 保存在程序目录下。"""
import json
import os
import shutil
import sys
from pathlib import Path

# Folder holding the program: next to the exe when frozen, the source root otherwise.
# 程序所在目录：打包后为 exe 所在目录，否则为源码根目录。
APP_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
CONFIG_PATH = APP_DIR / "config.json"

# The original SAK release, unpacked next to this folder, ships the CLI tools we drive.
# 解压在本文件夹旁边的原版 SAK 自带了本程序调用的命令行工具。
_SAK_BIN = APP_DIR.parent / "SAK_64bit" / "bin"

# Per-task temp folders; only folders named like this are ever deleted.
# 每个任务的临时文件夹；程序只会删除以此开头的文件夹。
JOB_PREFIX = "job_"

TOOLS = {
    "hactoolnet": "hactoolnet.exe",
    "4nxci": "4nxci.exe",
    "squirrel": "squirrel.exe",
    "hacbrewpack": "hacbrewpack.exe",
}


def _defaults() -> dict:
    tools = _SAK_BIN if _SAK_BIN.is_dir() else APP_DIR / "bin"
    return {
        "lang": "zh",
        "tools_dir": str(tools),
        "keys": str(tools / "prod.keys"),
        "output_dir": str(APP_DIR / "output"),
        "temp_dir": str(APP_DIR / "temp"),
        "nsz_level": 18,
        "geometry": None,
    }


class Config:
    def __init__(self):
        self.data = _defaults()
        if CONFIG_PATH.exists():
            try:
                self.data.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                pass

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def save(self):
        CONFIG_PATH.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")

    def tool(self, name: str) -> Path:
        return Path(self["tools_dir"]) / TOOLS[name]

    def tools_dir(self) -> Path:
        return Path(self["tools_dir"])

    def keys(self) -> Path:
        return Path(self["keys"])

    def temp(self, sub: str = "") -> Path:
        p = Path(self["temp_dir"]) / sub if sub else Path(self["temp_dir"])
        p.mkdir(parents=True, exist_ok=True)
        return p

    def purge_stale_temp(self) -> int:
        """Remove job folders left behind by a crash or forced quit. Touches nothing else.
        清理崩溃或强制退出后残留的任务文件夹，不碰其他任何内容。"""
        root = Path(self["temp_dir"])
        n = 0
        if root.is_dir():
            for d in root.iterdir():
                if d.is_dir() and d.name.startswith(JOB_PREFIX):
                    shutil.rmtree(d, ignore_errors=True)
                    n += 1
        return n

    def output(self, override: str = "") -> Path:
        p = Path(override or self["output_dir"])
        p.mkdir(parents=True, exist_ok=True)
        return p


def open_folder(path) -> None:
    path = str(path)
    if os.path.isdir(path):
        os.startfile(path)
