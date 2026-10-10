"""Sequential task queue.

A Task is a titled list of steps. A step is either an external process
(ProcStep, run through QProcess) or a Python callable (FuncStep, run in a
QThread). Steps of one task run in order; a failing step aborts the rest of
that task but the queue continues with the next task.

顺序执行的任务队列。
每个任务（Task）带标题和一组步骤。步骤可以是外部进程（ProcStep，通过 QProcess 运行），
也可以是 Python 函数（FuncStep，在 QThread 中运行）。同一任务的步骤按顺序执行；
某一步失败会中止该任务的剩余步骤，但队列会继续执行下一个任务。
"""
import locale
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Union

from PySide6.QtCore import QObject, QProcess, QThread, QTimer, Signal

_PERCENT = re.compile(r"(\d{1,3}(?:\.\d+)?)\s?%")
_ENC = locale.getpreferredencoding(False) or "utf-8"


@dataclass
class ProcStep:
    program: str
    args: List[str]
    cwd: Optional[str] = None


class StepContext:
    """Handed to FuncStep callables. / 传给 FuncStep 函数的上下文。"""

    def __init__(self, worker: "_FuncWorker"):
        self._w = worker

    def log(self, text: str):
        self._w.log.emit(text)

    def progress(self, cur: int, total: int):
        self._w.progress.emit(int(cur * 1000 / total) if total else -1)

    def cancelled(self) -> bool:
        return self._w.cancel_requested


@dataclass
class FuncStep:
    func: Callable[[StepContext], None]
    label: str = ""


@dataclass
class ExpandStep:
    """Runs on the GUI thread when reached; the steps it returns are inserted in its place.
    Used when the next commands depend on files produced by earlier steps.
    执行到时在界面线程运行，返回的步骤插入到它的位置。
    用于后续命令依赖前面步骤所产生文件的情况。"""
    func: Callable[[], List["Step"]]


@dataclass
class LogStep:
    """Writes a line to the log (used to explain automatic intermediate steps).
    向日志写一行（用于说明自动执行的中间步骤）。"""
    text: str


Step = Union[ProcStep, FuncStep, ExpandStep, LogStep]


@dataclass
class Task:
    title: str
    steps: List[Step] = field(default_factory=list)
    # Deleted when the task ends, whatever the outcome. / 任务结束时删除，无论成功与否。
    temp_dirs: List[Path] = field(default_factory=list)


class _FuncWorker(QThread):
    log = Signal(str)
    progress = Signal(int)

    def __init__(self, step: FuncStep):
        super().__init__()
        self.step = step
        self.cancel_requested = False
        self.ok = False

    def run(self):
        try:
            self.step.func(StepContext(self))
            self.ok = not self.cancel_requested
        except Exception as e:  # surfaced in the log, the task is marked failed / 写入日志，任务标为失败
            if type(e).__name__ == "OpError":  # deliberate, user-facing message / 主动给用户的提示
                self.log.emit(f"[!] {e}")
            else:
                self.log.emit(f"[error] {type(e).__name__}: {e}")
            self.ok = False


def _decode(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode(_ENC, errors="replace")


class TaskRunner(QObject):
    log = Signal(str)            # a finished output line / 完整的一行输出
    status = Signal(str)         # transient line (carriage-return progress output) / 临时行（用 \r 刷新的进度）
    progress = Signal(int)       # 0..1000, or -1 for busy / 0..1000，-1 表示忙碌
    task_started = Signal(str)
    queue_changed = Signal(int)  # tasks remaining, including the current one / 剩余任务数（含当前任务）
    all_done = Signal(bool, bool)  # (all_ok, cancelled) / （是否全部成功, 是否已取消）

    def __init__(self, parent=None):
        super().__init__(parent)
        self.queue: List[Task] = []
        self.current: Optional[Task] = None
        self.step_index = 0
        self.proc: Optional[QProcess] = None
        self.worker: Optional[_FuncWorker] = None
        self.all_ok = True
        self.cancelled = False
        self._buf = ""

    # ---- public API / 公开接口
    def busy(self) -> bool:
        return self.current is not None

    def submit(self, tasks: List[Task]):
        self.queue.extend(tasks)
        if not self.busy():
            self.all_ok, self.cancelled = True, False
            self._next_task()
        else:
            self.queue_changed.emit(len(self.queue) + 1)

    def cancel(self):
        if not self.busy():
            return
        self.cancelled = True
        self._remove_temps([d for t in self.queue for d in t.temp_dirs])
        self.queue.clear()
        if self.proc is not None:
            self.proc.kill()
        if self.worker is not None:
            self.worker.cancel_requested = True

    # ---- internals / 内部实现
    def _next_task(self):
        if not self.queue:
            self.current = None
            self.queue_changed.emit(0)
            self.all_done.emit(self.all_ok, self.cancelled)
            return
        self.current = self.queue.pop(0)
        self.step_index = 0
        self.queue_changed.emit(len(self.queue) + 1)
        self.task_started.emit(self.current.title)
        self.log.emit(f"\n▶ {self.current.title}")
        self._next_step()

    def _remove_temps(self, dirs: List[Path], attempt: int = 0):
        from .i18n import tr
        left = []
        for d in dirs:
            shutil.rmtree(d, ignore_errors=True)
            if d.exists():
                left.append(d)
        if not left:
            if dirs:
                self.log.emit(tr("temp_cleaned"))
            return
        if attempt < 3:  # a just-killed process may still hold handles for a moment / 刚被终止的进程可能还短暂占用文件
            QTimer.singleShot(2000, lambda: self._remove_temps(left, attempt + 1))
        else:
            self.log.emit(tr("temp_left", ", ".join(map(str, left))))

    def _finish_task(self, ok: bool, code: int = 0):
        from .i18n import tr
        self._remove_temps(list(self.current.temp_dirs))
        if ok:
            self.log.emit(tr("task_ok", self.current.title))
        else:
            self.all_ok = False
            self.log.emit(tr("task_fail", self.current.title, code))
        self._next_task()

    def _next_step(self):
        if self.cancelled:
            self._finish_task(False, -1)
            return
        if self.step_index >= len(self.current.steps):
            self._finish_task(True)
            return
        step = self.current.steps[self.step_index]
        self.step_index += 1
        if isinstance(step, LogStep):
            self.log.emit(step.text)
            self._next_step()
            return
        if isinstance(step, ExpandStep):
            try:
                new = step.func()
            except Exception as e:
                self.log.emit(f"[error] {type(e).__name__}: {e}")
                self._finish_task(False, -1)
                return
            self.current.steps[self.step_index:self.step_index] = new
            self._next_step()
            return
        self.progress.emit(-1)
        if isinstance(step, ProcStep):
            self._start_proc(step)
        else:
            self._start_func(step)

    def _start_proc(self, step: ProcStep):
        self.log.emit("$ " + " ".join(_quote(a) for a in [step.program, *step.args]))
        self._buf = ""
        self._last_status = ""
        p = QProcess(self)
        p.setProcessChannelMode(QProcess.MergedChannels)
        if step.cwd:
            p.setWorkingDirectory(step.cwd)
        p.readyReadStandardOutput.connect(self._on_output)
        p.finished.connect(self._on_proc_finished)
        p.errorOccurred.connect(self._on_proc_error)
        self.proc = p
        p.start(step.program, step.args)

    def _on_output(self):
        self._buf += _decode(bytes(self.proc.readAllStandardOutput()))
        # \r-terminated chunks are progress redraws: show transiently, parse %.
        # 以 \r 结尾的片段是进度刷新：只临时显示，并从中解析百分比。
        while True:
            m = re.search(r"[\r\n]", self._buf)
            if not m:
                break
            chunk, sep = self._buf[:m.start()], m.group()
            self._buf = self._buf[m.end():]
            if sep == "\r" and self._buf.startswith("\n"):
                self._buf, sep = self._buf[1:], "\n"
            chunk = chunk.rstrip()
            if not chunk:
                continue
            pm = _PERCENT.findall(chunk)
            if pm:
                self.progress.emit(min(1000, int(float(pm[-1]) * 10)))
            if sep == "\n":
                self.log.emit(chunk)
            else:
                self._last_status = chunk
                self.status.emit(chunk)

    def _on_proc_error(self, err):
        if err == QProcess.FailedToStart:
            self.log.emit(f"[error] failed to start: {self.proc.program()}")
            self._end_proc(False, -1)

    def _on_proc_finished(self, code, status):
        if self._buf.strip():
            self.log.emit(self._buf.strip())
        ok = status == QProcess.NormalExit and code == 0 and not self.cancelled
        if not ok and self._last_status:
            self.log.emit(self._last_status)
        self._end_proc(ok, code)

    def _end_proc(self, ok, code):
        if self.proc is None:
            return
        self.proc.deleteLater()
        self.proc = None
        if ok:
            self._next_step()
        else:
            self._finish_task(False, code)

    def _start_func(self, step: FuncStep):
        if step.label:
            self.log.emit(f"· {step.label}")
        w = _FuncWorker(step)
        w.log.connect(self.log)
        w.progress.connect(self.progress)
        w.finished.connect(self._on_func_finished)
        self.worker = w
        w.start()

    def _on_func_finished(self):
        w, self.worker = self.worker, None
        ok = w.ok
        w.deleteLater()
        if ok:
            self._next_step()
        else:
            self._finish_task(False, -1)


def _quote(a: str) -> str:
    return f'"{a}"' if (" " in a or not a) else a
