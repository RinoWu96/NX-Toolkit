"""Builds Task objects for each feature. Raises OpError for user-facing problems.
为各功能生成任务（Task）。遇到需要告知用户的问题时抛出 OpError。"""
import csv
import re
import shutil
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from struct import error as struct_error
from typing import List

from . import __version__, forwarder, split, updater, winexe
from .config import JOB_PREFIX, TOOLS_HOME, Config, tools_complete
from .i18n import tr
from .tasks import ExpandStep, FuncStep, LogStep, ProcStep, Task


class OpError(Exception):
    pass


def _need_tool(cfg: Config, name: str) -> str:
    p = cfg.tool(name)
    if not p.is_file():
        raise OpError(tr("missing_tool", p))
    return str(p)


def _need_keys(cfg: Config) -> str:
    if not cfg.keys().is_file():
        raise OpError(tr("missing_keys"))
    return str(cfg.keys())


def _job_temp(cfg: Config) -> Path:
    """A private per-task folder; the runner deletes it when the task ends (any outcome).
    每个任务专用的临时文件夹；任务结束时（无论结果如何）由任务队列删除。"""
    return cfg.temp(JOB_PREFIX + uuid.uuid4().hex[:8])


# ---------------------------------------------------------------- convert (XCI / NSP / NSZ / XCZ) / 格式互转
@dataclass
class NszOpts:
    level: int = 18
    long_mode: bool = False
    mode: str = "auto"        # auto | block | solid（自动 / 块 / 固实）
    threads: int = 0
    quick_verify: bool = True
    overwrite: bool = False


@dataclass
class ConvertOpts:
    keep_ncaid: bool = False
    rename: bool = False
    nsz: NszOpts = field(default_factory=NszOpts)


# Human-readable route per (input, target); mirrors _convert_steps below.
# 每种（输入, 目标）组合的路线说明，与下面的 _convert_steps 一一对应。
ROUTES = {
    (".xci", ".nsp"): "4NXCI",
    (".nsz", ".nsp"): "nsz -D",
    (".xcz", ".nsp"): "nsz -D → 4NXCI",
    (".nsp", ".xci"): "NSC_BUILDER",
    (".nsz", ".xci"): "nsz -D → NSC_BUILDER",
    (".xcz", ".xci"): "nsz -D",
    (".nsp", ".nsz"): "nsz -C",
    (".xci", ".nsz"): "4NXCI → nsz -C",
    (".xcz", ".nsz"): "nsz -D → 4NXCI → nsz -C",
    (".xci", ".xcz"): "nsz -C",
    (".nsp", ".xcz"): "NSC_BUILDER → nsz -C",
    (".nsz", ".xcz"): "nsz -D → NSC_BUILDER → nsz -C",
}


def _nsz_cmd() -> List[str]:
    # Frozen exe: the exe runs nsz itself (see app.py). Source: run nsz with this Python.
    # 打包后由 exe 自己运行 nsz（见 app.py）；源码运行时用当前 Python 调用 nsz。
    if getattr(sys, "frozen", False):
        return [sys.executable, "--run-nsz"]
    return [sys.executable, "-c", "import sys;sys.argv[0]='nsz';from nsz import main;main()"]


def _step_4nxci(cfg: Config, src: Path, outdir: Path, tmp: Path, o: ConvertOpts) -> ProcStep:
    args = ["-k", _need_keys(cfg), "-o", str(outdir), "-t", str(tmp / "4nxci")]
    if o.keep_ncaid:
        args.append("--keepncaid")
    if o.rename:
        args.append("-r")
    return ProcStep(_need_tool(cfg, "4nxci"), args + [str(src)], cwd=str(tmp))


def _squirrel_cwd(cfg: Config) -> str:
    """squirrel (NSC_BUILDER) only reads keys from ./keys.txt and writes a DB/ folder into its cwd,
    so it runs in a dedicated folder holding a copy of the configured prod.keys.
    squirrel（NSC_BUILDER）只从当前目录的 keys.txt 读取密钥，还会在当前目录写入 DB 文件夹，
    所以让它在专用目录里运行，并在其中放一份设置里 prod.keys 的副本。"""
    keys = Path(_need_keys(cfg))
    work = cfg.temp("squirrel")
    dst = work / "keys.txt"
    if not dst.is_file() or dst.read_bytes() != keys.read_bytes():
        shutil.copyfile(keys, dst)
    return str(work)


def _squirrel_exe(cfg: Config) -> str:
    """Path of a UTF-8 copy of squirrel (made once, kept in temp/squirrel); the original otherwise.
    返回 squirrel 的 UTF-8 副本路径（只生成一次，放在 temp/squirrel）；做不到时返回原版。
    Without it, Korean and other non-GBK game titles crash squirrel on Chinese Windows (see winexe).
    没有副本时，中文 Windows 上遇到韩文等 GBK 之外的游戏名，squirrel 会崩溃（见 winexe）。"""
    src = Path(_need_tool(cfg, "squirrel"))
    if not winexe.supports_utf8_codepage():
        return str(src)
    work = cfg.temp("squirrel")
    dst, stamp = work / "squirrel_utf8.exe", work / "squirrel_utf8.src"
    st = src.stat()
    sig = f"{src}|{st.st_size}|{int(st.st_mtime)}"
    if dst.is_file() and stamp.is_file() and stamp.read_text(encoding="utf-8") == sig:
        return str(dst)
    try:
        winexe.make_utf8_copy(src, dst)
        stamp.write_text(sig, encoding="utf-8")
        return str(dst)
    except (OSError, ValueError, struct_error):
        return str(src)


def _step_to_xci(cfg: Config, src: Path, outdir: Path) -> ProcStep:
    args = ["-o", str(outdir), "-t", "xci", "-dc", str(src)]
    return ProcStep(_squirrel_exe(cfg), args, cwd=_squirrel_cwd(cfg))


def _step_nsz(cfg: Config, srcs: List[Path], outdir: Path, tmp: Path, compress: bool, n: NszOpts) -> ProcStep:
    args = ["--keys", _need_keys(cfg), "-o", str(outdir)]
    if n.overwrite:
        args.append("-w")
    if compress:
        args += ["-C", "-l", str(n.level)]
        if n.long_mode:
            args.append("-L")
        if n.mode == "block":
            args.append("-B")
        elif n.mode == "solid":
            args.append("-S")
        if n.threads:
            args += ["-t", str(n.threads)]
        if n.quick_verify:
            args.append("-Q")
    else:
        args.append("-D")
    cmd = _nsz_cmd()
    return ProcStep(cmd[0], cmd[1:] + args + [str(s) for s in srcs], cwd=str(tmp))


def _then_each(folder: Path, ext: str, make) -> ExpandStep:
    """After earlier steps have filled `folder`, run make(files) on every *ext in it.
    等前面的步骤把文件写入 folder 后，再对其中所有 *ext 文件执行 make(files)。"""
    def expand():
        found = sorted(folder.glob(f"*{ext}"))
        if not found:
            raise FileNotFoundError(f"no {ext} produced in {folder}")
        return make(found)
    return ExpandStep(expand)


def _convert_steps(cfg: Config, src: Path, target: str, outdir: Path, tmp: Path, o: ConvertOpts):
    """Steps turning src into `target` (one of .nsp .xci .nsz .xcz), chaining through temp folders.
    生成把 src 转成 target（.nsp .xci .nsz .xcz 之一）的步骤，需要时经由临时文件夹串联多步。"""
    ext = src.suffix.lower()
    mid = tmp / "mid"
    mid2 = tmp / "mid2"
    for d in (mid, mid2):
        d.mkdir(parents=True, exist_ok=True)
    n = o.nsz
    if target == ".nsp":
        if ext == ".xci":
            return [_step_4nxci(cfg, src, outdir, tmp, o)]
        if ext == ".nsz":
            return [_step_nsz(cfg, [src], outdir, tmp, False, n)]
        if ext == ".xcz":
            return [_step_nsz(cfg, [src], mid, tmp, False, n),
                    _then_each(mid, ".xci", lambda fs: [_step_4nxci(cfg, f, outdir, tmp, o) for f in fs])]
    if target == ".xci":
        if ext == ".nsp":
            return [_step_to_xci(cfg, src, outdir)]
        if ext == ".nsz":
            return [_step_nsz(cfg, [src], mid, tmp, False, n),
                    _then_each(mid, ".nsp", lambda fs: [_step_to_xci(cfg, f, outdir) for f in fs])]
        if ext == ".xcz":
            return [_step_nsz(cfg, [src], outdir, tmp, False, n)]
    if target == ".nsz":
        if ext == ".nsp":
            return [_step_nsz(cfg, [src], outdir, tmp, True, n)]
        if ext == ".xci":
            return [_step_4nxci(cfg, src, mid, tmp, o),
                    _then_each(mid, ".nsp", lambda fs: [_step_nsz(cfg, fs, outdir, tmp, True, n)])]
        if ext == ".xcz":
            return [_step_nsz(cfg, [src], mid, tmp, False, n),
                    _then_each(mid, ".xci", lambda fs: [_step_4nxci(cfg, f, mid2, tmp, o) for f in fs]),
                    _then_each(mid2, ".nsp", lambda fs: [_step_nsz(cfg, fs, outdir, tmp, True, n)])]
    if target == ".xcz":
        if ext == ".xci":
            return [_step_nsz(cfg, [src], outdir, tmp, True, n)]
        if ext == ".nsp":
            return [_step_to_xci(cfg, src, mid),
                    _then_each(mid, ".xci", lambda fs: [_step_nsz(cfg, fs, outdir, tmp, True, n)])]
        if ext == ".nsz":
            return [_step_nsz(cfg, [src], mid, tmp, False, n),
                    _then_each(mid, ".nsp", lambda fs: [_step_to_xci(cfg, f, mid2) for f in fs]),
                    _then_each(mid2, ".xci", lambda fs: [_step_nsz(cfg, fs, outdir, tmp, True, n)])]
    return None


_TITLE_ID = re.compile(r"\[([0-9A-Fa-f]{16})\]")


def content_kind(path: Path) -> str:
    """'base', 'update', 'dlc' from the [titleid] in the file name, or '' if there is none.
    Updates are base|0x800; DLC have any other non-zero low 12 bits.
    根据文件名中的 [titleid] 判断是本体、更新包还是 DLC；没有 Title ID 时返回 ''。
    更新包 = 本体 | 0x800；DLC 的低 12 位为其他非零值。"""
    m = _TITLE_ID.search(path.name)
    if not m:
        return ""
    low = int(m.group(1), 16) & 0xFFF
    return "base" if low == 0 else "update" if low == 0x800 else "dlc"


def _report_outputs(outdir: Path, target: str):
    """First/last step pair: remember when the task started, then list what it produced.
    一对首尾步骤：记录任务开始时间，结束时列出实际生成的文件。"""
    state = {}

    def mark(ctx):
        state["t"] = time.time() - 2

    def report(ctx):
        new = [p for p in outdir.iterdir() if p.is_file() and p.stat().st_mtime >= state["t"]]
        for p in new:
            ctx.log(tr("output_file", p))
        if not any(p.suffix.lower() == target for p in new):
            ctx.log(tr("output_mismatch", target[1:].upper(),
                       ", ".join(sorted({p.suffix[1:].upper() for p in new})) or "-"))
    return FuncStep(mark), FuncStep(report)


def _fail_step(message: str) -> FuncStep:
    def run(ctx):
        raise OpError(message)
    return FuncStep(run)


def convert(cfg: Config, files: List[str], outdir: Path, target: str, opts: ConvertOpts) -> List[Task]:
    _need_keys(cfg)
    tasks = []
    for f in map(Path, files):
        ext = f.suffix.lower()
        label = f"{ext[1:].upper()} → {target[1:].upper()}  {f.name}"
        if ext == target:
            tasks.append(Task(label, [FuncStep(lambda ctx, f=f: ctx.log(tr("convert_same", f.name)))]))
            continue
        kind = content_kind(f)
        if target in (".xci", ".xcz") and kind in ("update", "dlc"):
            tasks.append(Task(label, [_fail_step(tr("xci_needs_base", tr("kind_" + kind)))]))
            continue
        tmp = _job_temp(cfg)
        steps = _convert_steps(cfg, f, target, outdir, tmp, opts)
        if steps is None:
            continue
        mark, report = _report_outputs(outdir, target)
        tasks.append(Task(label, [mark, *_annotate(ext, target, steps), report], temp_dirs=[tmp]))
    return tasks


# What each stage turns its input into (mirrors the tools' behaviour).
# 每个阶段把输入转成什么格式（与各工具的实际行为一致）。
_STAGE_OUT = {
    "nsz -D": {".nsz": ".nsp", ".xcz": ".xci"},
    "nsz -C": {".nsp": ".nsz", ".xci": ".xcz"},
    "4NXCI": {".xci": ".nsp"},
    "NSC_BUILDER": {".nsp": ".xci"},
}


def _annotate(ext: str, target: str, steps: list) -> list:
    """For chained routes, log the plan and put a "[i/n] tool: A -> B" line before each stage.
    _convert_steps returns exactly one step per stage of ROUTES (checked by tests).
    多步路线：先在日志写出整体计划，每个阶段前加一行「[i/n] 工具：A → B」。
    _convert_steps 为 ROUTES 的每个阶段恰好生成一个步骤（已有测试验证）。"""
    stages = ROUTES[(ext, target)].split(" → ")
    if len(stages) == 1:
        return steps
    out = [LogStep(tr("chain_plan", ROUTES[(ext, target)]))]
    cur = ext
    for i, (stage, step) in enumerate(zip(stages, steps), 1):
        nxt = _STAGE_OUT[stage][cur]
        line = tr("chain_stage", i, len(stages), stage, cur[1:].upper(), nxt[1:].upper())
        out += [LogStep(line + (tr("chain_tmp") if i < len(stages) else "")), step]
        cur = nxt
    return out


# ---------------------------------------------------------------- merge / 合并
def merge(cfg: Config, files: List[str], outdir: Path, fmt: str) -> List[Task]:
    if len(files) < 2:
        raise OpError(tr("merge_need2"))
    _need_keys(cfg)
    exe = _squirrel_exe(cfg)
    paths = [Path(f) for f in files]
    label = f"Merge → {fmt.upper()}  {paths[0].stem} (+{len(paths) - 1})"

    kinds = [content_kind(p) for p in paths]
    steps = [LogStep(tr("merge_inputs"))]
    steps += [LogStep(f"    · {tr('kind_name_' + (k or 'unknown'))}:  {p.name}") for p, k in zip(paths, kinds)]
    if fmt == "xci" and all(kinds) and "base" not in kinds:
        return [Task(label, steps + [_fail_step(tr("merge_no_base"))])]

    tmp = _job_temp(cfg)
    mid = tmp / "mid"
    mid.mkdir()
    packed = [p for p in paths if p.suffix.lower() in (".nsz", ".xcz")]
    plain = [p for p in paths if p not in packed]
    if packed:
        # squirrel may not read NSZ/XCZ, so decompress them first / squirrel 可能读不了 NSZ/XCZ，先解压
        steps.append(LogStep(tr("merge_decompress", len(packed))))
        steps.append(_step_nsz(cfg, packed, mid, tmp, False, NszOpts()))

    def run_merge():
        inputs = plain + sorted(p for p in mid.iterdir() if p.suffix.lower() in (".nsp", ".xci"))
        if len(inputs) < len(paths):
            raise FileNotFoundError(tr("merge_missing", len(paths), len(inputs)))
        listfile = tmp / "mlist.txt"
        listfile.write_text("\n".join(map(str, inputs)) + "\n", encoding="utf-8")
        args = ["-t", fmt, "-o", str(outdir), "-tfile", str(listfile), "-roma", "TRUE", "-dmul", "calculate"]
        return [LogStep(tr("merge_start", len(inputs), fmt.upper())), ProcStep(exe, args, cwd=_squirrel_cwd(cfg))]

    mark, report = _report_outputs(outdir, "." + fmt)
    return [Task(label, [mark, *steps, ExpandStep(run_merge), report], temp_dirs=[tmp])]


# ---------------------------------------------------------------- split / join / 拆分与合并分卷
def split_join(cfg: Config, files: List[str], outdir: Path, do_split: bool) -> List[Task]:
    tasks = []
    for f in map(Path, files):
        if do_split:
            if f.suffix.lower() == ".nsp" and f.parent.resolve() == outdir.resolve():
                raise OpError(tr("split_same_dir"))
            if f.is_file() and not split.needs_split(f):
                tasks.append(Task(f"Split  {f.name}", [FuncStep(lambda ctx, f=f: ctx.log(tr("split_small", f.name)))]))
                continue
            tasks.append(Task(f"Split  {f.name}", [FuncStep(lambda ctx, f=f: split.split_file(f, outdir, ctx))]))
        else:
            tasks.append(Task(f"Join  {f.name}", [FuncStep(lambda ctx, f=f: split.join_parts(f, outdir, ctx))]))
    return tasks


# ---------------------------------------------------------------- firmware / 固件
def _identify_fw(cfg: Config, fwdir: Path, ctx) -> None:
    mapping = cfg.tools_dir() / "fw_nca_mapping.csv"
    ncas = {p.stem.split(".")[0].lower() for p in fwdir.glob("*.nca")}
    ctx.log(f"  {len(ncas)} NCA(s) in {fwdir}")
    if mapping.is_file():
        with open(mapping, newline="", encoding="utf-8") as fh:
            for row in csv.reader(fh, delimiter=";"):
                if len(row) >= 2 and row[1].strip().lower() in ncas:
                    ctx.log(tr("fw_version", row[0]))
                    return
    ctx.log(tr("fw_unknown"))


def firmware(cfg: Config, files: List[str], outdir: Path) -> List[Task]:
    keys = _need_keys(cfg)
    exe = _need_tool(cfg, "hactoolnet")
    tasks = []
    for f in map(Path, files):
        fwdir = outdir / f"{f.stem}_firmware"
        args = ["-k", keys, "--disablekeywarns", "-t", "xci", "--updatedir", str(fwdir), str(f)]
        tasks.append(Task(f"Firmware  {f.name}", [
            ProcStep(exe, args, cwd=str(cfg.tools_dir())),
            FuncStep(lambda ctx, d=fwdir: _identify_fw(cfg, d, ctx)),
        ]))
    return tasks


# ---------------------------------------------------------------- savegames / 存档
def savegames(cfg: Config, files: List[str], outdir: Path) -> List[Task]:
    exe = _need_tool(cfg, "hactoolnet")
    keys = cfg.keys()
    tasks = []
    for f in map(Path, files):
        args = (["-k", str(keys)] if keys.is_file() else []) + \
               ["--disablekeywarns", "-t", "save", "--outdir", str(outdir / f.name), str(f)]
        tasks.append(Task(f"Save  {f.name}", [ProcStep(exe, args, cwd=str(cfg.tools_dir()))]))
    return tasks


# ---------------------------------------------------------------- forwarder / 转发器
def nro_forwarder(cfg: Config, outdir: Path, *, name: str, publisher: str, version: str,
                  title_id: str, sd_path: str, icon: bytes, screenshot: bool, video: bool,
                  startup_user: bool) -> List[Task]:
    keys = _need_keys(cfg)
    exe = _need_tool(cfg, "hacbrewpack")
    tools = cfg.tools_dir()
    for req in ("nro_fw_main", "nro_fw_main.npdm"):
        if not (tools / req).is_file():
            raise OpError(tr("missing_tool", tools / req))
    tmp = _job_temp(cfg)
    build, nspdir = tmp / "build", tmp / "nsp"
    nacp = forwarder.build_nacp(name, publisher, version, screenshot, video, startup_user)

    def prepare(ctx):
        forwarder.prepare_build_dir(build, tools, sd_path, nacp, icon)
        ctx.log(f"  title id {title_id}, target {sd_path}")

    args = ["-k", keys,
            "--exefsdir", str(build / "exefs"), "--romfsdir", str(build / "romfs"),
            "--controldir", str(build / "control"), "--logodir", str(build / "logo"),
            "--tempdir", str(tmp / "hbp_temp"), "--backupdir", str(tmp / "hbp_backup"),
            "--nspdir", str(nspdir), "--titleid", title_id,
            "--titlename", name, "--titlepublisher", publisher or "Homebrew"]
    if not (tools / "nro_fw_NintendoLogo.png").exists():
        args.append("--nologo")

    def collect(ctx):
        safe = "".join(c for c in name if c not in '\\/:*?"<>|').strip() or title_id
        for nsp in nspdir.glob("*.nsp"):
            dst = outdir / f"{safe} [{title_id}].nsp"
            shutil.move(str(nsp), dst)
            ctx.log(f"  = {dst}")

    return [Task(f"NRO forwarder  {name}", [
        FuncStep(prepare),
        ProcStep(exe, args, cwd=str(tmp)),
        FuncStep(collect),
    ], temp_dirs=[tmp])]


# ---------------------------------------------------------------- tools download / update check / 工具下载与更新检查
def download_tools(cfg: Config) -> List[Task]:
    """Fetch the latest SAK release into ./tools and point Settings at it (keys untouched).
    下载最新 SAK 发布包到 ./tools，并把设置里的工具目录指向它（不动密钥）。"""
    tmp = _job_temp(cfg)

    def run(ctx):
        updater.install_tools(TOOLS_HOME, tmp, ctx, lambda key, *a: ctx.log("  " + tr(key, *a)))
        cfg["tools_dir"] = str(TOOLS_HOME)
        cfg.save()

    return [Task(tr("task_download_tools"), [FuncStep(run)], temp_dirs=[tmp])]


def check_updates(cfg: Config, result: dict) -> List[Task]:
    """Compare installed tools and this app with the latest releases; findings go to `result`.
    比较已安装工具和本程序与最新发布版本；结果写入 result。"""
    def run(ctx):
        tag, _, size = updater.latest_sak()
        have = updater.installed_tools_version(cfg.tools_dir())
        if have == tag:
            ctx.log("  " + tr("tools_uptodate", tag))
        elif not have and tools_complete(cfg.tools_dir()):
            # Installed by hand (no version record): don't nag. / 手动安装、无版本记录：不催促重新下载。
            ctx.log("  " + tr("tools_manual", tag))
        else:
            result["tools"] = tag
            ctx.log("  " + tr("tools_update_avail", have or tr("unknown"), tag))
        app = updater.latest_app()
        if app:
            result["app"] = app
            ctx.log("  " + tr("app_update_avail", __version__, app))
        else:
            ctx.log("  " + tr("app_uptodate", __version__))

    return [Task(tr("task_check_updates"), [FuncStep(run)])]
